from contextlib import contextmanager


@contextmanager
def driver(root):
    from neo4j import GraphDatabase

    from ..config import Settings

    settings = Settings.load(root)
    password = settings.secret("neo4j")
    if not password:
        raise ValueError("Neo4j credentials are not configured")
    instance = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, password),
        connection_timeout=5,
        connection_acquisition_timeout=5,
        max_connection_pool_size=8,
        max_transaction_retry_time=5,
    )
    try:
        yield instance
    finally:
        instance.close()


def write_nodes(tx, label, rows, namespace):
    """Validate identities before upsert; return actual database counters."""
    from ..graph.schema import LABELS

    if label not in LABELS:
        raise ValueError("Node label outside schema")
    if any(
        type(r.get("id")) is not int
        or r["id"] <= 0
        or not isinstance(r.get("name"), str)
        or not r["name"].strip()
        for r in rows
    ):
        raise ValueError("Invalid node identity/name; no partial node batch accepted")
    result = tx.run(
        f"UNWIND $rows AS row MERGE (n:{label} {{id:row.id}}) SET n += row RETURN count(n) AS matched",
        rows=[{**r, "dataset": namespace} for r in rows],
    )
    matched = result.single(strict=True)["matched"]
    counters = result.consume().counters
    return {
        "input_count": len(rows),
        "created_or_matched_count": matched,
        "invalid_count": 0,
        "nodes_created": counters.nodes_created,
        "relationships_created": counters.relationships_created,
        "properties_set": counters.properties_set,
    }


def write_relationships(tx, group, rows, namespace):
    """Reject missing endpoints inside the transaction instead of silently losing rows."""
    from ..graph.schema import GROUPS

    if group not in GROUPS:
        raise ValueError("Relationship outside schema")
    left, relation, right = group
    unique = {(r["left"], r["right"]) for r in rows}
    if any(type(a) is not int or type(b) is not int or a <= 0 or b <= 0 for a, b in unique):
        raise ValueError("Invalid relationship identity")
    payload = [{"left": a, "right": b} for a, b in sorted(unique)]
    counts = tx.run(
        f"UNWIND $rows AS row OPTIONAL MATCH (a:{left} {{id:row.left,dataset:$scope}}) "
        f"OPTIONAL MATCH (b:{right} {{id:row.right,dataset:$scope}}) "
        "RETURN sum(CASE WHEN a IS NULL THEN 1 ELSE 0 END) AS missing_start, "
        "sum(CASE WHEN b IS NULL THEN 1 ELSE 0 END) AS missing_end",
        rows=payload,
        scope=namespace,
    ).single(strict=True)
    if counts["missing_start"] or counts["missing_end"]:
        raise ValueError(
            f"Missing endpoints: start={counts['missing_start']}, end={counts['missing_end']}; transaction rolled back"
        )
    counters = (
        tx.run(
            f"UNWIND $rows AS row MATCH (a:{left} {{id:row.left,dataset:$scope}}),"
            f"(b:{right} {{id:row.right,dataset:$scope}}) MERGE (a)-[r:{relation}]->(b) SET r.dataset=$scope",
            rows=payload,
            scope=namespace,
        )
        .consume()
        .counters
    )
    return {
        "input_count": len(rows),
        "created_or_matched_count": len(unique),
        "missing_start": 0,
        "missing_end": 0,
        "duplicates": len(rows) - len(unique),
        "nodes_created": counters.nodes_created,
        "relationships_created": counters.relationships_created,
        "properties_set": counters.properties_set,
    }
