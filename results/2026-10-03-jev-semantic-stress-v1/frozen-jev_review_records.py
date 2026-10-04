"""Recover every bounded semantic judgment from the saved MCP run trace.

The immediate run_capability response is a preview. Never use that preview as
the full batch result, even when the run itself reports completion.
"""


def complete_reviews(trace: dict, items: list[dict], bindings: dict, capability: dict) -> dict:
    """Require exact coverage and provenance before returning candidate reviews.

    This workload has at most twelve items, retrieved with a twenty-item limit.
    A remaining cursor or unexpected item is an integrity failure, not permission
    to omit reviews. Failed provider judgments remain failed and cannot approve.
    """
    expected = {item["id"]: item["data"] for item in items}
    if len(expected) != len(items) or set(expected) != set(bindings):
        raise ValueError("Duplicate or mismatched expected review IDs")
    manifest = trace["manifest"]["capability"]
    if any(manifest.get(key) != value for key, value in capability.items()):
        raise ValueError("Stored reviewer identity changed")
    rows = trace["items"]
    byid = {row["id"]: row for row in rows}
    if trace.get("nextCursor") is not None or len(byid) != len(rows) or set(byid) != set(expected):
        raise ValueError("Incomplete, duplicate or unexpected review trace coverage")
    questions = manifest["definition"]["stages"][0]["questions"]
    reviews = {}
    for item_id, data in expected.items():
        row, binding = byid[item_id], bindings[item_id]
        if row["data"] != data or row["result"]["id"] != item_id:
            raise ValueError("Stored item differs from the submitted review")
        result = row["result"]
        review = binding | {"status": result["status"], "runId": trace["runId"], "item_id": item_id}
        if result["status"] == "complete":
            events = row["events"]
            if len(events) != 1 or events[0]["request"]["state"] != {"item": data, "context": {}, "prior": {}}:
                raise ValueError("Unexpected provider state or stage count")
            if events[0]["request"]["questions"] != questions or events[0]["cached"]:
                raise ValueError("Changed reviewer question or unexpected cached judgment")
            answer = result["stages"]["review"]["answers"]["relation"]
            review.update(choice=answer["choice"], confidence=answer["confidence"],
                          returned_model=events[0]["response"]["model"])
        reviews.setdefault(binding["case_id"], []).append(review)
    return reviews
