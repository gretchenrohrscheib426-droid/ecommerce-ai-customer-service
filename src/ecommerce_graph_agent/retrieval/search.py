"""Canonical metadata is structured; fused scores are ranks, never probabilities."""

import unicodedata

from .indexes import INDEXES


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def metadata(row):
    return {
        "canonical_id": row["canonical_id"],
        "canonical_name": row["name"],
        "label": row["label"],
        "id": row["id"],
    }


class Retriever:
    def __init__(self, instance, embedder, aliases=None, min_cosine=0.65):
        self.driver = instance
        self.embedder = embedder
        self.aliases = aliases or {}
        self.min_cosine = min_cosine

    def catalog(self):
        with self.driver.session(database="neo4j", default_access_mode="READ") as session:
            return [
                dict(r)
                for r in session.run(
                    "MATCH (n) WHERE any(l IN labels(n) WHERE l IN $labels) RETURN n.id AS id,n.canonical_id AS canonical_id,n.name AS name,labels(n)[0] AS label",
                    labels=list(INDEXES),
                )
            ]

    def exact(self, text, label=None):
        if label is not None and label not in INDEXES:
            raise ValueError("Unsupported entity label")
        norm = normalized(text)
        return [
            metadata(r)
            for r in self.catalog()
            if (label is None or r["label"] == label) and normalized(r["name"]) == norm
        ]

    def hybrid(self, text, label=None, top_k=5):
        if label is not None and label not in INDEXES:
            raise ValueError("Unsupported entity label")
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 120 or not 1 <= top_k <= 10:
            raise ValueError("Invalid retrieval request")
        vector = self.embedder.encode([text], query=True)[0]
        combined: dict[str, dict] = {}
        # Escape Lucene operators by making the entire user fragment a quoted literal.
        literal = '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
        with self.driver.session(database="neo4j", default_access_mode="READ") as session:
            for kind, prefix in INDEXES.items():
                if label and label != kind:
                    continue
                for mode, index, query, params in [
                    (
                        "vector",
                        prefix + "_embedding_index",
                        "CALL db.index.vector.queryNodes($index,$k,$vector) YIELD node,score RETURN node.id AS id,node.canonical_id AS canonical_id,node.name AS name,labels(node)[0] AS label,score",
                        {"k": top_k, "vector": vector},
                    ),
                    (
                        "fulltext",
                        prefix + "_full_text_index",
                        "CALL db.index.fulltext.queryNodes($index,$text,{limit:$k}) YIELD node,score RETURN node.id AS id,node.canonical_id AS canonical_id,node.name AS name,labels(node)[0] AS label,score LIMIT $k",
                        {"k": top_k, "text": literal},
                    ),
                ]:
                    from neo4j import Query

                    rows = session.run(Query(query, timeout=5), index=index, **params)
                    for rank, row in enumerate(rows, 1):
                        key = row["canonical_id"]
                        entry = combined.setdefault(
                            key,
                            {"text": row["name"], "metadata": metadata(row), "score": 0.0, "channels": {}},
                        )
                        entry["score"] += 1 / (60 + rank)
                        entry["channels"][mode] = float(row["score"])
        return sorted(combined.values(), key=lambda x: (-x["score"], x["metadata"]["canonical_id"]))[:top_k]

    def align(self, text, label=None):
        exact = self.exact(text, label)
        if len(exact) == 1:
            return {"status": "aligned", "method": "exact", "entity": exact[0], "candidates": exact}
        if len(exact) > 1:
            return {"status": "clarify", "method": "duplicate-name", "candidates": exact}
        alias = self.aliases.get(normalized(text))
        if alias:
            matching = [
                metadata(r)
                for r in self.catalog()
                if r["canonical_id"] in alias and (not label or r["label"] == label)
            ]
            if len(matching) != len(alias):
                raise ValueError("Approved alias has unresolved canonical ID")
            if len(matching) == 1:
                return {
                    "status": "aligned",
                    "method": "reviewed-alias",
                    "entity": matching[0],
                    "candidates": matching,
                }
            return {"status": "clarify", "method": "ambiguous-alias", "candidates": matching}
        candidates = self.hybrid(text, label)
        viable = [
            r
            for r in candidates
            if r["channels"].get("vector", 0) >= self.min_cosine or "fulltext" in r["channels"]
        ]
        if not viable:
            return {"status": "no_match", "method": "hybrid", "candidates": []}
        # Tiny development data cannot support a calibrated automatic fuzzy match.
        # Ask the user even for a single approximate candidate instead of selecting rank 1.
        return {
            "status": "clarify",
            "method": "hybrid-confirmation-required",
            "candidates": [x["metadata"] for x in viable],
            "ranked": viable,
        }
