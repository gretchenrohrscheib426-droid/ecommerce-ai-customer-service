"""Five label-specific BGE/vector + CJK fulltext pairs; preserve compatible indexes."""

import hashlib
import json
from pathlib import Path

from ..db.neo4j import driver

INDEXES = {
    "SPU": "spu",
    "BaseTrademark": "trademark",
    "Category3": "category3",
    "Category2": "category2",
    "Category1": "category1",
}
BGE_REVISION = "7999e1d3359715c523056ef9478215996d62a620"


class Embedder:
    def __init__(self, root, device="cpu"):
        import torch
        from sentence_transformers import SentenceTransformer

        torch.set_num_threads(4)
        self.model = SentenceTransformer(
            str(Path(root) / "artifacts/local/models/bge-small-zh-v1.5"), local_files_only=True, device=device
        )
        if self.model.get_sentence_embedding_dimension() != 512:
            raise ValueError("BGE dimension must be measured as 512")

    def encode(self, texts, query=False):
        # Explicit BGE model-card retrieval instruction only for queries; stored names stay unprefixed.
        if query:
            texts = ["为这个句子生成表示以用于检索相关文章：" + text for text in texts]
        result = self.model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        if result.shape != (len(texts), 512):
            raise ValueError("Unexpected vector shape")
        return result.tolist()


def check_index(row, label, kind):
    prop = "embedding" if kind == "VECTOR" else "name"
    if (
        row["type"] != kind
        or row["entityType"] != "NODE"
        or row["labelsOrTypes"] != [label]
        or row["properties"] != [prop]
    ):
        raise ValueError("Existing index schema incompatible; explicit scoped migration required")
    config = row["options"]["indexConfig"]
    if kind == "VECTOR" and (
        config.get("vector.dimensions") != 512
        or str(config.get("vector.similarity_function", "")).lower() != "cosine"
        or row["options"]["indexProvider"] != "vector-2.0"
    ):
        raise ValueError("Existing vector provider/config incompatible")
    if kind == "FULLTEXT" and (
        config.get("fulltext.analyzer") != "cjk" or row["options"]["indexProvider"] != "fulltext-1.0"
    ):
        raise ValueError("Existing fulltext analyzer/provider incompatible")


def create_indexes(instance, embedder):
    report: dict = {
        "status": "passed",
        "model_revision": BGE_REVISION,
        "dimension": 512,
        "normalized": True,
        "query_instruction": "为这个句子生成表示以用于检索相关文章：",
        "fulltext_analyzer": "cjk",
        "encoded_nodes": 0,
        "created": [],
        "reused": [],
    }
    with instance.session(database="neo4j") as session:
        for label in INDEXES:
            rows = [
                dict(r)
                for r in session.run(
                    f"MATCH (n:{label}) RETURN n.id AS id,n.name AS name,n.embedding_text_hash AS hash,n.embedding_model AS model,n.embedding AS embedding"
                )
            ]
            changed = [
                r
                for r in rows
                if r["hash"] != hashlib.sha256(r["name"].encode()).hexdigest()
                or r["model"] != BGE_REVISION
                or not r["embedding"]
                or len(r["embedding"]) != 512
            ]
            if changed:
                vectors = embedder.encode([r["name"] for r in changed])
                payload = [
                    {"id": r["id"], "vector": v, "hash": hashlib.sha256(r["name"].encode()).hexdigest()}
                    for r, v in zip(changed, vectors, strict=True)
                ]
                session.run(
                    f"UNWIND $rows AS row MATCH (n:{label} {{id:row.id}}) SET n.embedding=row.vector,n.embedding_text_hash=row.hash,n.embedding_model=$revision",
                    rows=payload,
                    revision=BGE_REVISION,
                ).consume()
                report["encoded_nodes"] += len(changed)
        existing = {
            r["name"]: dict(r)
            for r in session.run(
                "SHOW INDEXES YIELD name,type,entityType,labelsOrTypes,properties,options,state RETURN *"
            )
        }
        for label, prefix in INDEXES.items():
            for kind, suffix in [("FULLTEXT", "full_text_index"), ("VECTOR", "embedding_index")]:
                name = f"{prefix}_{suffix}"
                if name in existing:
                    check_index(existing[name], label, kind)
                    report["reused"].append(name)
                elif kind == "VECTOR":
                    session.run(
                        f"CREATE VECTOR INDEX {name} IF NOT EXISTS FOR (n:{label}) ON n.embedding OPTIONS {{indexConfig: {{`vector.dimensions`:512,`vector.similarity_function`:'cosine'}}}}"
                    ).consume()
                    report["created"].append(name)
                else:
                    session.run(
                        f"CREATE FULLTEXT INDEX {name} IF NOT EXISTS FOR (n:{label}) ON EACH [n.name] OPTIONS {{indexConfig: {{`fulltext.analyzer`:'cjk'}}}}"
                    ).consume()
                    report["created"].append(name)
        session.run("CALL db.awaitIndexes(120)").consume()
        rows = [
            dict(r)
            for r in session.run(
                "SHOW INDEXES YIELD name,type,entityType,labelsOrTypes,properties,options,state RETURN *"
            )
        ]
        selected = []
        for label, prefix in INDEXES.items():
            for kind, suffix in [("FULLTEXT", "full_text_index"), ("VECTOR", "embedding_index")]:
                row = next(r for r in rows if r["name"] == f"{prefix}_{suffix}")
                check_index(row, label, kind)
                if row["state"] != "ONLINE":
                    raise RuntimeError("Index not ONLINE")
                selected.append(row)
        report["indexes"] = selected
    return report


if __name__ == "__main__":
    root = Path.cwd()
    embedder = Embedder(root)
    with driver(root) as d:
        first = create_indexes(d, embedder)
        second = create_indexes(d, embedder)
    if second["encoded_nodes"] != 0 or second["created"]:
        raise AssertionError("Index build not idempotent")
    report = {"status": "passed", "first": first, "second": second}
    (root / "reports/private/indexes.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "indexes_online": len(first["indexes"]),
                "encoded": first["encoded_nodes"],
                "second_encoded": second["encoded_nodes"],
            }
        )
    )
