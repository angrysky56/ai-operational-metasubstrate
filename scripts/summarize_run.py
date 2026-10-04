"""Export descriptive runtime, answer-length, and case-score records after rating.

Reads the treatment map, so use only after condition-masked ratings are sealed.
These summaries do not modify ratings or add statistical endpoints.
"""

import argparse
import json
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path


def summarize(run: Path, ratings_path: Path) -> dict:
    """Summarize persisted attempts and join saved ratings to complete answers."""
    events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines() if line.strip()]
    starts = [event for event in events if event["event"] == "started"]
    ends = [event for event in events if event["event"] == "finished"]
    packet = json.loads((run / "rating-packet.json").read_text())
    map_rows = json.loads((run / "rating-map.json").read_text())
    rating_rows = json.loads(ratings_path.read_text())
    mapping = {row["label"]: row for row in map_rows}
    ratings = {row["label"]: row for row in rating_rows}
    labels = {row["label"] for row in packet}
    if len(labels) != len(packet) or len(mapping) != len(map_rows) or len(ratings) != len(rating_rows):
        raise ValueError("Duplicate labels")
    if set(mapping) != labels or set(ratings) != labels:
        raise ValueError("Packet, map, and ratings must have identical label coverage")
    dataset = json.loads((run / "dataset.json").read_text())
    by_cell = {event["cell"]: event for event in ends}
    if len(by_cell) != len(ends):
        raise ValueError("This summary expects at most one terminal attempt per cell")
    style = {}
    for condition in dataset["conditions"]:
        answers = [row for row in packet if mapping[row["label"]]["condition"] == condition]
        durations = [by_cell[mapping[row["label"]]["cell"]]["elapsed_seconds"] for row in answers]
        lengths = [len(row["answer"].split()) for row in answers]
        style[condition] = {
            "responses": len(answers), "answer_words_total": sum(lengths),
            "answer_words_mean": statistics.mean(lengths) if lengths else None,
            "answer_words_median": statistics.median(lengths) if lengths else None,
            "request_seconds_total": sum(durations),
            "request_seconds_median": statistics.median(durations) if durations else None,
        }
    case_scores = [
        {**mapping[row["label"]], **ratings[row["label"]], "answer_words": len(row["answer"].split())}
        for row in packet
    ]
    (run / "scores-by-case.json").write_text(
        json.dumps(sorted(case_scores, key=lambda row: (row["case_id"], row["condition"])), indent=2) + "\n"
    )
    return {
        "attempts": len(starts), "finished": len(ends),
        "statuses": dict(Counter(event["status"] for event in ends)),
        "request_seconds_total": sum(event["elapsed_seconds"] for event in ends),
        "wall_seconds_first_start_to_last_finish": (
            datetime.fromisoformat(ends[-1]["at"]) - datetime.fromisoformat(starts[0]["at"])
        ).total_seconds() if starts and ends else None,
        "median_request_seconds": statistics.median(event["elapsed_seconds"] for event in ends) if ends else None,
        "load_seconds_total": sum(event["raw"].get("load_duration", 0) / 1e9 for event in ends),
        "generated_tokens_total": sum(event["raw"].get("eval_count", 0) for event in ends),
        "returned_thinking_count": sum(bool(event["raw"].get("message", {}).get("thinking")) for event in ends),
        "style_by_condition": style,
    }


def main() -> None:
    """Save descriptive summaries without changing frozen inputs or ratings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--ratings", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.run, args.ratings)
    (args.run / "runtime-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
