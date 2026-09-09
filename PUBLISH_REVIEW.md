# GitHub 源码发布审查

结论以同目录 release_validation.json 的当前门禁为准；本次逐文件清单见 publish_manifest.json。只有门禁 READY、暂存区清单一致且历史/秘密检查通过才推送。

目标：现有 PUBLIC 仓库 gretchenrohrscheib426-droid/ecommerce-ai-customer-service，目标 main。旧 main 的备份 archive/pre-knowledge-graph-upgrade-20260909 已先上传，原 SHA 为 1dd9fa782994d81a72f7b4c8c991fec22ef419b4。工作分支 codex/knowledge-graph-portfolio-upgrade，保留历史，正常合并，禁止 force push。此次发布由明确的用户请求授权。

发布：完整 src、annotation 接口、configs、scripts、tests、envs、独立 data/sample、examples、文档、CI、MIT/NOTICE/第三方许可说明，以及真实公开样例截图。旧仓库的配置、工作流、状态说明由当前图谱实现的文档替代，备份分支保留原件。

不发布：课程 DOCX/ZIP、内嵌教程/架构原图、SQL、标注全文、原前端 vendor、安装器、模型权重/缓存、数据库、Conda/venv、凭据、个人字段、绝对个人路径和运行日志。清单外内容不推送；未知再分发许可默认排除。

许可：MIT 仅覆盖有权公开的代码和独立合成样例，课程来源保留，第三方许可证不被项目 MIT 覆盖。依赖许可证元数据见 docs/dependency_licenses.json，固定版本及来源见 THIRD_PARTY_NOTICES.md。没有捆绑第三方运行时或模型。

验证：固定模板/端点/身份/索引/跨度/前端安全均有回归；真实 MySQL/Neo4j、BGE、HTTP、浏览器、重启与干净目录安装分别记录。依赖升级后重新扫描完整分发集合，不忽略漏洞。启发式秘密扫描不是不存在秘密的数学证明，还需审查暂存差异。

未验证：正式模型训练与 F1、真实 AI 预标注和 DeepSeek、Label Studio 新环境人工验收、Docker、生产部署。随机 tiny 模型只用于接口测试；不将其作为正式 best_model。源码发布不表示网站上线或企业落地。
