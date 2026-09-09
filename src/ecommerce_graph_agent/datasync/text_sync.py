"""Replace owned SPU description mentions with stable source/span identity."""

import hashlib

from .reconciliation import ensure_namespace, snapshot
from .validate import digest


def sync_tags(instance, predictions, namespace):
    """Atomically replace only the current SPU's owned description mentions."""
    from ..models.ner.process import validate_record

    with instance.session(database="neo4j") as session:
        ensure_namespace(session, namespace)
        before = snapshot(session)
        for item in predictions:
            text = item["text"]
            spans = validate_record({"text": text, "label": item["spans"]})
            if hashlib.sha256(text.encode()).hexdigest() != item["source_sha256"]:
                raise ValueError("Source text hash mismatch")
            rows = []
            for span in spans:
                key = digest(
                    [
                        namespace,
                        item["spu_id"],
                        "description",
                        item["source_sha256"],
                        span["start"],
                        span["end"],
                    ]
                )
                rows.append(
                    {
                        "id": key,
                        "canonical_id": "Tag:" + key,
                        "name": span["text"],
                        "start": span["start"],
                        "end": span["end"],
                        "source_field": "description",
                        "source_hash": item["source_sha256"],
                        "model_version": item["model_sha256"],
                        "spu_id": item["spu_id"],
                        "dataset": namespace,
                        "semantic_review": item.get("semantic_review", "not_human_gold"),
                    }
                )

            def transaction(tx):
                source = tx.run(
                    "MATCH (s:SPU {id:$id,dataset:$scope}) RETURN s.description AS text",
                    id=item["spu_id"],
                    scope=namespace,
                ).single(strict=True)
                if source["text"] != text:
                    raise ValueError("Graph SPU description differs from extraction source")
                tx.run(
                    'MATCH (:SPU {id:$id,dataset:$scope})-[:Have]->(t:Tag {dataset:$scope,source_field:"description"}) WHERE NOT t.id IN $ids DETACH DELETE t',
                    id=item["spu_id"],
                    scope=namespace,
                    ids=[r["id"] for r in rows],
                ).consume()
                tx.run(
                    "MATCH (s:SPU {id:$id,dataset:$scope}) UNWIND $rows AS row MERGE (t:Tag {id:row.id}) SET t += row MERGE (s)-[r:Have]->(t) SET r.dataset=$scope",
                    id=item["spu_id"],
                    scope=namespace,
                    rows=rows,
                ).consume()

            session.execute_write(transaction)
        after = snapshot(session)
    return {
        "status": "passed",
        "before": before,
        "after": after,
        "spu_count": len(predictions),
        "input_mentions": sum(len(x["spans"]) for x in predictions),
    }
