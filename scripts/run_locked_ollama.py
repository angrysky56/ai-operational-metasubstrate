"""Run new Ornith evaluations with locked settings and observed pre-output order.

Linux/Colab Python 3.10+. Refuses cloud aliases, never downloads a model, never
retries a wrong answer, and counts every persisted request start against budget.
The dataset contains rater keys, but only system text and visible case prompts
are sent to the model. This runner does not score scientific outcomes.
"""

import argparse
import fcntl
import hashlib
import json
import os
import random
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def settings_lock() -> dict:
    """Read the explicit model/settings policy; changed policy needs a new freeze."""
    return json.loads((ROOT / "data/generator-settings-lock.json").read_text())


def pre_output_rule() -> str:
    """Use identical observable check instructions in every prompt condition."""
    return (ROOT / "data/pre-output-checks-v1.txt").read_text().strip()


class ChatStreamError(ValueError):
    """Retain partial output when a streaming request fails."""

    def __init__(self, message: str, partial: dict):
        super().__init__(message)
        self.partial = partial


def assemble_stream(chunks: Any) -> dict:
    """Collect exact thinking/answer text and audit their observed chunk order."""
    thinking, content, raw = [], [], {}
    audit = {"chunks": 0, "thinking_chunks": 0, "answer_chunks": 0,
             "first_thinking": None, "first_answer": None, "thinking_after_answer": False,
             "mixed_chunk": False}
    for chunk in chunks:
        if not isinstance(chunk, dict) or chunk.get("error"):
            raise ValueError("Invalid Ollama streaming chunk")
        index = audit["chunks"]
        audit["chunks"] += 1
        message = chunk.get("message", {})
        if not isinstance(message, dict):
            raise ValueError("Invalid streaming message")
        thought, answer = message.get("thinking", ""), message.get("content", "")
        if not isinstance(thought, str) or not isinstance(answer, str):
            raise ValueError("Invalid streaming text")
        if thought:
            if audit["first_thinking"] is None:
                audit["first_thinking"] = index
            audit["thinking_after_answer"] |= audit["first_answer"] is not None
            audit["thinking_chunks"] += 1
            thinking.append(thought)
        if answer:
            if audit["first_answer"] is None:
                audit["first_answer"] = index
            audit["answer_chunks"] += 1
            content.append(answer)
        audit["mixed_chunk"] |= bool(thought and answer)
        raw.update({key: value for key, value in chunk.items() if key != "message"})
        if message.get("tool_calls"):
            raw["unexpected_tool_calls"] = True
    audit["pass"] = (audit["first_thinking"] is not None and audit["first_answer"] is not None
                     and audit["first_thinking"] < audit["first_answer"]
                     and not audit["thinking_after_answer"] and not audit["mixed_chunk"])
    raw["message"] = {"role": "assistant", "thinking": "".join(thinking), "content": "".join(content)}
    raw["pre_output_audit"] = audit
    return raw


def stream_chat(base: str, payload: dict, timeout: float) -> dict:
    """Use curl's absolute deadline and preserve the actual NDJSON stream."""
    process = subprocess.Popen(["curl", "--silent", "--show-error", "--no-buffer", "--fail-with-body",
        "--max-time", str(timeout), "--noproxy", "*", "-H", "Content-Type: application/json",
        "--data-binary", "@-", base + "/api/chat"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    process.stdin.write(json.dumps(payload))
    process.stdin.close()
    partial = {}
    try:
        partial = assemble_stream(json.loads(line) for line in process.stdout if line.strip())
        code = process.wait(timeout=5)
        error = process.stderr.read()
        if code:
            raise ChatStreamError("Ollama stream transport failed: " + error.strip(), partial)
        return partial
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def stamp() -> str:
    """Return an unambiguous UTC event timestamp."""
    return datetime.now(timezone.utc).isoformat()


def digest(value: bytes) -> str:
    """Hash exact input bytes for reproducibility."""
    return hashlib.sha256(value).hexdigest()


def api(base: str, route: str, payload: dict | None = None, timeout: float = 10) -> dict:
    """Call local Ollama without inheriting proxy configuration."""
    if route == "/api/chat":
        return stream_chat(base, payload, timeout)
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(base + route, data=data, headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        result = json.load(response)
    if not isinstance(result, dict) or result.get("error"):
        raise ValueError(f"Invalid Ollama response: {result}")
    return result


def local_model(tags: dict, name: str) -> dict:
    """Require an installed generation model whose metadata does not route remotely."""
    matches = [m for m in tags["models"] if m.get("name") == name]
    if len(matches) != 1:
        raise ValueError("Model must match exactly one installed model name")
    model = matches[0]
    if model.get("remote_host") or model.get("remote_model") or "cloud" in name.lower():
        raise ValueError("Cloud aliases are not permitted by this local runner")
    if not model.get("digest"):
        raise ValueError("Model digest is required")
    return model


def read_events(path: Path) -> list[dict]:
    """Read checkpoints strictly; a damaged log is never silently discarded."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append(path: Path, event: dict) -> None:
    """Flush each event before making or completing an inference request."""
    with path.open("a") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def budget_state(events: list[dict]) -> tuple[int, float, set[str]]:
    """Count attempts, completed request time, and terminal cells; refuse uncertain starts."""
    starts = {e["attempt"]: e for e in events if e["event"] == "started"}
    ends = {e["attempt"]: e for e in events if e["event"] == "finished"}
    if starts.keys() - ends.keys():
        raise ValueError("Unfinished request in checkpoint; do not resubmit an uncertain attempt")
    if ends.keys() - starts.keys():
        raise ValueError("Checkpoint contains a finish without a request start")
    return len(starts), sum(e["elapsed_seconds"] for e in ends.values()), {e["cell"] for e in ends.values()}


def messages_for(dataset: dict, cell: dict) -> list[dict]:
    """Compose only visible inputs; scoring keys and family metadata stay outside the request."""
    case = next(c for c in dataset["cases"] if c["id"] == cell["case_id"])
    history = case.get("history", [])
    if not isinstance(history, list):
        raise ValueError("Case history must be a list")
    visible_history = []
    for index, turn in enumerate(history):
        expected_role = "user" if index % 2 == 0 else "assistant"
        if not isinstance(turn, dict) or turn.get("role") != expected_role or not isinstance(turn.get("content"), str):
            raise ValueError("Fixed history must contain alternating user/assistant text turns")
        visible_history.append({"role": turn["role"], "content": turn["content"]})
    if len(history) % 2:
        raise ValueError("Fixed history must end with an assistant turn")
    system = dataset["conditions"][cell["condition"]]
    rule = pre_output_rule()
    if not system.endswith(rule):
        system += "\n\n" + rule
    return [
        {"role": "system", "content": system},
        *visible_history,
        {"role": "user", "content": case["prompt"]},
    ]


def response_status(raw: dict) -> str:
    """Separate completed answers, output-budget exhaustion, and invalid payloads."""
    message = raw.get("message", {})
    if not raw.get("done") or not isinstance(message, dict):
        return "invalid"
    if raw.get("done_reason") in ("length", "max_tokens"):
        return "truncated"
    if not raw.get("pre_output_audit", {}).get("pass") or raw.get("unexpected_tool_calls"):
        return "invalid"
    if message.get("tool_calls") or not isinstance(message.get("content"), str) or not message["content"].strip():
        return "invalid"
    return "complete"


def export(out: Path, dataset: dict, manifest: dict, events: list[dict]) -> None:
    """Write a reviewer packet without treatment labels plus a separate mapping."""
    lookup = {cell["id"]: cell for cell in manifest["order"]}
    completed = [e for e in events if e["event"] == "finished" and e["status"] == "complete"]
    random.Random(manifest["config"]["order_seed"] + 1).shuffle(completed)
    packet, mapping = [], []
    for index, event in enumerate(completed, 1):
        cell = lookup[event["cell"]]
        case = next(c for c in dataset["cases"] if c["id"] == cell["case_id"])
        label = f"answer-{index:03}"
        packet.append({"label": label, "history": case.get("history", []), "task": case["prompt"], "key": case["key"], "requirements": case.get("requirements", []), "metric_scope": case.get("metric_scope", {}), "answer": event["raw"]["message"]["content"]})
        mapping.append({"label": label, "cell": cell["id"], "case_id": case["id"], "condition": cell["condition"]})
    (out / "rating-packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    (out / "rating-map.json").write_text(json.dumps(mapping, indent=2) + "\n")


def main() -> None:
    """Validate frozen inputs, then execute sequentially within persistent attempt/time limits."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/development.json")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--max-attempts", type=int, default=18)
    parser.add_argument("--max-seconds", type=int, default=7200)
    parser.add_argument("--limit-new", type=int, default=18)
    parser.add_argument("--request-timeout", type=int, default=600)
    parser.add_argument("--num-predict", type=int, default=8192)
    parser.add_argument("--num-ctx", type=int, default=16384)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--order-seed", type=int, default=20261003)
    parser.add_argument("--think", choices=("true", "false"), default="true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    policy = settings_lock()
    if (args.model != policy["model"] or args.think != "true" or args.num_ctx != 16384
            or args.num_predict != 8192 or args.seed != policy["options"]["seed"]):
        parser.error("This collector locks Ornith thinking on, context 16384, cap 8192 and seed 42")
    base = args.base_url.rstrip("/")
    url = urlparse(base)
    if url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost", "::1") or url.username or url.password or url.path or url.query or url.fragment:
        parser.error("Only an HTTP loopback Ollama endpoint is supported")
    if min(args.max_attempts, args.max_seconds, args.limit_new, args.request_timeout, args.num_predict, args.num_ctx) <= 0:
        parser.error("All budgets and limits must be positive")
    dataset_bytes = args.dataset.read_bytes()
    dataset = json.loads(dataset_bytes)
    if dataset.get("schema") != 1 or not dataset.get("conditions") or not dataset.get("cases"):
        raise ValueError("Unsupported or empty dataset")
    ids = [c["id"] for c in dataset["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case IDs")
    model = local_model(api(base, "/api/tags"), args.model)
    if model["digest"] != policy["digest"]:
        raise ValueError("Locked generator digest changed; do not mix model versions")
    show = api(base, "/api/show", {"model": args.model})
    if show.get("remote_host") or show.get("remote_model"):
        raise ValueError("Selected model resolves to a remote host")
    if "completion" not in show.get("capabilities", []):
        raise ValueError("Selected model lacks completion capability")
    version = api(base, "/api/version")
    config = {
        "model": args.model, "digest": model["digest"], "backend": version,
        "base_url": base, "dataset_sha256": digest(dataset_bytes),
        "runner_sha256": digest(Path(__file__).read_bytes()),
        "settings_lock_sha256": digest((ROOT / "data/generator-settings-lock.json").read_bytes()),
        "pre_output_rule_sha256": digest((ROOT / "data/pre-output-checks-v1.txt").read_bytes()),
        "stream": True,
        "max_attempts": args.max_attempts, "max_seconds": args.max_seconds,
        "request_timeout": args.request_timeout, "order_seed": args.order_seed,
        "think": args.think == "true",
        "options": {"temperature": 0, "seed": args.seed, "num_predict": args.num_predict, "num_ctx": args.num_ctx, "top_k": 20, "top_p": 0.95},
    }
    for case in dataset["cases"]:
        eligible = case.get("conditions", list(dataset["conditions"]))
        if not isinstance(eligible, list) or not eligible or len(set(eligible)) != len(eligible) or any(p not in dataset["conditions"] for p in eligible):
            raise ValueError("Invalid eligible case conditions")
    order = [{"id": f"{c['id']}-{p}", "case_id": c["id"], "condition": p} for c in dataset["cases"] for p in c.get("conditions", dataset["conditions"])]
    random.Random(args.order_seed).shuffle(order)
    if args.dry_run:
        print(json.dumps({"config": config, "planned_cells": len(order), "first_cells": order[:args.limit_new]}, indent=2))
        return
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out / ".run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest_path = out / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            if manifest["config"] != config:
                raise ValueError("Resume configuration changed; use original settings or a new run directory")
            if digest((out / "dataset.json").read_bytes()) != config["dataset_sha256"]:
                raise ValueError("Frozen dataset snapshot changed")
        else:
            if (out / "events.jsonl").exists():
                raise ValueError("Event log exists without manifest")
            manifest = {"created_at": stamp(), "config": config, "order": order, "model_metadata": model, "show": show}
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            (out / "dataset.json").write_bytes(dataset_bytes)
        event_path = out / "events.jsonl"
        events = read_events(event_path)
        attempts, spent, terminal = budget_state(events)
        new = 0
        session_start = time.monotonic()
        for cell in manifest["order"]:
            if cell["id"] in terminal:
                continue
            remaining = args.max_seconds - spent - (time.monotonic() - session_start)
            if attempts >= args.max_attempts or new >= args.limit_new or remaining <= 0:
                print("Stopped at invocation, attempt, or cumulative time limit", flush=True)
                break
            payload = {"model": args.model, "messages": messages_for(dataset, cell), "stream": True, "think": config["think"], "options": config["options"], "keep_alive": "5m"}
            attempts += 1
            new += 1
            append(event_path, {"event": "started", "attempt": attempts, "cell": cell["id"], "at": stamp(), "request": payload})
            print(f"Request {attempts}/{args.max_attempts}: {cell['id']}", flush=True)
            start = time.monotonic()
            raw: dict[str, Any] = {}
            try:
                raw = api(base, "/api/chat", payload, timeout=min(args.request_timeout, remaining))
                status, error = response_status(raw), None
            except BaseException as exc:
                raw = getattr(exc, "partial", raw)
                status, error = "error", f"{type(exc).__name__}: {exc}"
            elapsed = time.monotonic() - start
            append(event_path, {"event": "finished", "attempt": attempts, "cell": cell["id"], "at": stamp(), "elapsed_seconds": elapsed, "status": status, "error": error, "raw": raw})
            print(f"  {status}: {elapsed:.1f}s; generated tokens={raw.get('eval_count')}", flush=True)
            if status != "complete":
                print("Stopped for review; no automatic retry", flush=True)
                break
        events = read_events(event_path)
        export(out, dataset, manifest, events)
        counts = {}
        for e in events:
            if e["event"] == "finished":
                counts[e["status"]] = counts.get(e["status"], 0) + 1
        print(json.dumps({"finished": counts, "output": str(out)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
