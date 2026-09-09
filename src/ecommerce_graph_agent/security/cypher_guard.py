"""Positive grammar boundary: accept only exact audited read templates.

This is deliberately stricter than a keyword blacklist. Comments, CALL, multiple
statements, write clauses and unbounded traversals all fail the same allowlist.
"""

from ..graph.queries import TEMPLATES


def validate_query(query, parameters):
    if not isinstance(query, str) or query not in TEMPLATES.values():
        raise ValueError("Cypher outside exact tested template subset")
    if (
        set(parameters) != {"entity_id", "limit"}
        or type(parameters["entity_id"]) is not int
        or parameters["entity_id"] <= 0
    ):
        raise ValueError("Invalid canonical entity parameter")
    if type(parameters["limit"]) is not int or not 1 <= parameters["limit"] <= 20:
        raise ValueError("Invalid result bound")
    return query, parameters
