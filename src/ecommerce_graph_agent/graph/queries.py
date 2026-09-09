"""Exact approved templates, typed parameters, fixed DB and timeout. No raw HTTP API."""

from neo4j import Query

TEMPLATES = {
    "attributes:SPU": "MATCH (s:SKU)-[:Belong]->(p:SPU {id:$entity_id}) OPTIONAL MATCH (s)-[:Have]->(v:SaleAttrValue)<-[:Have]-(a:SaleAttr) RETURN p.canonical_id AS source_id,p.name AS product,s.canonical_id AS sku_id,s.name AS sku,a.name AS attribute,v.name AS value ORDER BY s.id,a.id,v.id LIMIT $limit",
    "category_path:SPU": "MATCH (p:SPU {id:$entity_id})-[:Belong]->(c3:Category3)-[:Belong]->(c2:Category2)-[:Belong]->(c1:Category1) RETURN p.canonical_id AS source_id,p.name AS product,c1.name AS category1,c2.name AS category2,c3.name AS category3 LIMIT $limit",
    "product_detail:SPU": "MATCH (p:SPU {id:$entity_id}) OPTIONAL MATCH (p)-[:Belong]->(b:BaseTrademark) OPTIONAL MATCH (p)-[:Belong]->(c:Category3) RETURN p.canonical_id AS source_id,p.name AS product,p.description AS description,b.name AS brand,c.name AS category LIMIT $limit",
    "price:SPU": "MATCH (s:SKU)-[:Belong]->(p:SPU {id:$entity_id}) RETURN p.canonical_id AS source_id,p.name AS product,s.canonical_id AS sku_id,s.name AS sku,s.price AS price,s.is_sale AS is_sale ORDER BY toFloat(s.price),s.id LIMIT $limit",
    "tags:SPU": "MATCH (p:SPU {id:$entity_id})-[:Have]->(t:Tag) RETURN p.canonical_id AS source_id,p.name AS product,t.id AS mention_id,t.name AS tag,t.start AS start,t.end AS end,t.source_hash AS source_hash,t.model_version AS model_version,t.semantic_review AS semantic_review ORDER BY t.start LIMIT $limit",
    "products:BaseTrademark": "MATCH (p:SPU)-[:Belong]->(b:BaseTrademark {id:$entity_id}) RETURN p.canonical_id AS source_id,p.name AS product,b.name AS brand ORDER BY p.id LIMIT $limit",
    "products:Category3": "MATCH (p:SPU)-[:Belong]->(c:Category3 {id:$entity_id}) RETURN p.canonical_id AS source_id,p.name AS product,c.name AS category ORDER BY p.id LIMIT $limit",
    "products:Category2": "MATCH (p:SPU)-[:Belong]->(:Category3)-[:Belong]->(c:Category2 {id:$entity_id}) RETURN p.canonical_id AS source_id,p.name AS product,c.name AS category ORDER BY p.id LIMIT $limit",
    "products:Category1": "MATCH (p:SPU)-[:Belong]->(:Category3)-[:Belong]->(:Category2)-[:Belong]->(c:Category1 {id:$entity_id}) RETURN p.canonical_id AS source_id,p.name AS product,c.name AS category ORDER BY p.id LIMIT $limit",
}


def compile_plan(plan, entity, limit=20):
    from ..security.cypher_guard import validate_query

    intent = plan.intent
    if intent == "products" and entity["label"] == "SPU":
        intent = "product_detail"
    key = intent + ":" + entity["label"]
    if key not in TEMPLATES:
        raise ValueError("Intent/entity type combination unsupported")
    return validate_query(TEMPLATES[key], {"entity_id": entity["id"], "limit": limit})


def execute(instance, query, parameters):
    from ..security.cypher_guard import validate_query

    validate_query(query, parameters)
    with instance.session(database="neo4j", default_access_mode="READ") as session:
        # Neo4j 5 driver accepts Query(timeout=...) on session.run, not transaction.run.
        rows = [dict(r) for r in session.run(Query(query, timeout=5), **parameters)]
    if len(rows) > 20:
        raise RuntimeError("Result limit invariant violated")
    return rows
