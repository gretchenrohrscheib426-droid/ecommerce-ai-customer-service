# 简历与证据

项目性质：**基于课程项目二次开发的电商知识图谱本地演示**。只使用自己能讲清、且对应检查通过的条目；代码生成和测试通过不自动代表本人掌握。

|候选表述|代码|验证证据|不能扩大为|
|---|---|---|---|
|实现结构数据同步、端点校验和重复导入对账|src/ecommerce_graph_agent/datasync|tests/unit/test_data.py、test_neo4j_writer.py；真实 graph_sync 集成|生产规模与企业落地|
|实现 BGE/全文候选融合与同名澄清|retrieval/search.py、entity_alignment.py、web/service.py|test_hybrid_retrieval.py、test_entity_alignment.py、真实 HTTP 报告|大规模召回率提升|
|将图查询限制在固定模板、受校验参数与只读业务库|qa/cypher.py、security/cypher_guard.py|test_cypher_guard.py、public_verify.py 写入拒绝|绝对安全或生产权限体系|
|修复 BERT 分词与原文跨度映射、模型及分词器保存|models/ner/process.py、train.py、predict.py|test_ner_alignment.py、test_transformers_contract.py|已完成正式训练或高 F1|
|补齐 FastAPI、静态前端、错误路径和可重启交付|web/、scripts/services.py、run_demo.py|API 单测、chat_browser.mjs、public_verify.py --restart|网站已经部署|

课程主线与个人变更逐项见 SOURCE_MAP。真实结果状态见 release_validation.json 与 GitHub Actions；私有本机日志不公开，其中包含解释器和运行路径。面试应现场展示同名澄清、数据库证据、无匹配与拒绝写入，而不是背诵虚构指标。
