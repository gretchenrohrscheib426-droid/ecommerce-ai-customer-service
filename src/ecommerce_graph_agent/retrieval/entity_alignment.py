"""Public alignment contract: exact/approved alias or explicit confirmation."""


def align_entity(retriever, query, label=None):
    result = retriever.align(query, label)
    entity = result.get("entity", {})
    ranked = result.get("ranked", [])
    return {
        "query": query,
        "label": label,
        "status": {"aligned": "resolved", "clarify": "ambiguous", "no_match": "not_found"}[result["status"]],
        "canonical_id": entity.get("canonical_id"),
        "canonical_name": entity.get("canonical_name"),
        "score": ranked[0]["score"] if ranked else None,
        "score_type": "RRF rank, not probability; exact/alias uses null",
        "method": result["method"],
        "candidates": result.get("candidates", []),
    }
