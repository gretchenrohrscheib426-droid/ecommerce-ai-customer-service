# 来源、实现与证据

课程范围来自已完整读取的主讲义（提取文本 1–944）、内嵌 Neo4j 教程（1–626）、Label Studio 教程（1–156）与配套 ZIP。原件和读取范围日志在父级私有工作区；以下实现路径均相对本公开仓库。公开实现为重新编写，不分发课程原代码。

|来源分类|来源或问题|当前实现|回归证据|
|---|---|---|---|
|COURSE_BASELINE|标题标注、AI预标注链路|annotation/ml_backend/model.py、_wsgi.py；configs/label_studio.xml|test_annotation.py、test_annotation_http.py（独立 SDK 环境）|
|REIMPLEMENTED|课程 BERT TAG process/train/predict/evaluate|models/ner/{process,train,predict,eval}.py|test_ner.py、test_split.py；当前修订正式训练未运行|
|FIXED|677重叠、范围/标签/重复、UTF-16|models/ner/data_validation.py、process.py|test_ner_validation.py、test_annotation.py；原记录保留在私有审计|
|FIXED|tokenizer 与原文对齐、特殊token -100|models/ner/process.py tokenize_with_offsets / align_labels|test_ner_alignment.py、test_ner.py；新策略字符 words + word_ids|
|FIXED|保存分词器和来源、缺模型不回退|models/ner/train.py、predict.py、eval.py|test_ner.py；BLOCKED_MODEL_NOT_TRAINED实际命令|
|REIMPLEMENTED|MySQL读取与结构图同步|datasync/mysql_reader.py、table_sync.py|test_mysql_connection.py、test_graph_sync.py|
|FIXED|36/14缺端点、重复关系、改名身份|datasync/validate.py、neo4j_writer.py、reconciliation.py|test_data.py、test_neo4j_writer.py、test_graph_sync.py|
|FIXED|Tag 来源、描述哈希、限定替换|datasync/text_sync.py|test_data.py；原版私有真实图测试另存父工作区|
|FIXED|索引幂等和512维校验|graph/indexes.py、constraints.py|test_indexes.py；真实重复建索引报告|
|REIMPLEMENTED|BGE+全文混合检索|retrieval/search.py、hybrid.py|test_hybrid_retrieval.py|
|FIXED|实体metadata与同名歧义|retrieval/entity_alignment.py、schemas.py|test_entity_alignment.py、test_workflow.py|
|FIXED|参数化只读模板、行数、超时|graph/queries.py、security/cypher_guard.py|test_cypher_guard.py、test_qa.py；真实只读拒写|
|REIMPLEMENTED|DeepSeek解析与答案生成|llm/deepseek_client.py、prompts.py|mock协议测试；真实在线未运行|
|ORIGINAL_EXTENSION|有界工具工作流与一次性澄清|agent/orchestrator.py、intent.py、state.py|test_workflow.py、test_chat_pipeline.py|
|FIXED|旧前端CDN依赖和不安全HTML|web/static/{index.html,app.js,styles.css}|tests/e2e/chat_browser.mjs 真实浏览器与故障注入分别记录|
|ORIGINAL_EXTENSION|配置、健康探测、日志|config.py、health.py、logging_config.py|test_config.py、test_api_schemas.py、tests/e2e/test_api.py|
|ORIGINAL_EXTENSION|独立样例、Windows启动、发布边界|scripts/、data/sample/、.github/|test_public_boundary.py；release_validation.json|

表中 models、datasync 等模块前缀均为 src/ecommerce_graph_agent/；test_*.py 的单元文件在 tests/unit/，数据库文件在 tests/integration/。db/、qa/、retrieval/indexes.py 保留为兼容导出，实际职责以新模块为准。

课程静态预期 1529/1641 只针对清理规则明确后的结构图，不能当导入结果。父级私有旧版真实导入与训练证据保留；公开当前修订使用 21/27 结构图和 4/4 人工 Tag。新对齐策略不继承旧版 F1 验收。


## 本次公开发布的新增修复

|问题|修复代码|回归证据|
|---|---|---|
|旧训练依赖存在已知漏洞；Transformers 5 接口变化|pyproject.toml、models/ner/train.py；移除废弃参数，显式 TensorBoard writer|test_transformers_contract.py：随机微型模型两步训练、保存重载；不是正式模型成绩|
|CPU torch 被常规 PyPI 审计跳过|scripts/audit_dependencies.py；审计完整已安装包及上游 torch 版本|release_validation.json dependency_audit；无忽略项|
|原生服务端口写死、MySQL 停止导入不存在模块|services.py、sample_demo.py、public_verify.py、configure_demo_mysql.py|test_runtime_configuration.py；原生 MySQL 初始化、实际同步与停止重启|
|跳过全部测试的 XML 被误判成功|validate_release.py junit_status|test_release_gate.py 空报告、全跳过和失败报告|
|独立后端漏装共享跨度校验包|scripts/install_ml_backend.py 安装当前轻量项目|test_ml_backend_install.py；独立新环境 7 项 SDK 协议测试|
|公共边界缺数据库与新虚拟环境规则|check_public_boundary.py、.gitignore|test_public_boundary.py；候选、暂存与可达历史实际扫描|
|旧 README 无法代表完整代码，Windows 大小写路径影响 Linux|README、中英文运行文档、docs/ARCHITECTURE.md、CI workflows|清单校验、干净目录安装与远端 Actions|

课程学习主线与上述个人新增必须分别说明。公开版本没有继承旧私有模型的 F1，也没有将随机 smoke 模型充作 best_model。
