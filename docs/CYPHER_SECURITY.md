# Cypher 查询安全

Cypher 是 Neo4j 图查询语言。HTTP 接口只收 Question，不收 query。graph/queries.py 中的 9 个固定模板是唯一可执行查询集合；security/cypher_guard.py 要求查询文本精确属于集合，并校验实体 ID、limit 类型和范围。模板参数单独传入驱动，不拼接用户名称。

当前规则包括：拒绝写入、CALL/APOC、LOAD CSV、注释拼接、分号附加查询、UNION、自定义 MATCH 和缺失 LIMIT。不是靠删几个危险关键词“清洗”任意查询，而是未在白名单的文本均拒绝。

实体 ID 必须为正整数，bool 不算 int；limit 为 1–20。已确认的实体类型与意图决定模板，参数不能由未经验证的模型覆盖。驱动绑定固定 neo4j 数据库，查询超时 5 秒，结果受行数上限控制。应用启动检查该库实际只读。

test_cypher_guard.py 包含多类注入与参数类型反例；test_workflow.py 检查澄清与模型计划绑定。服务只读探针是真实数据库拒写，mock 测试不替代它。

这些措施服务于本地示例。Neo4j Community 的账号仍具有 system 库权限，本地端口与进程边界十分必要；不宣称已具备生产多租户授权。不要为了方便添加 /query 或透传 LLM Cypher。
