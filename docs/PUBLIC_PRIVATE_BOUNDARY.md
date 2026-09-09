# 公开与私有边界

目标是现有公开仓库 `gretchenrohrscheib426-droid/ecommerce-ai-customer-service` 的 main。旧主分支先保留在 archive/pre-knowledge-graph-upgrade-20260909；开发在 codex/knowledge-graph-portfolio-upgrade，验证后正常推送，禁止 force push。

公开内容：源代码、配置名称、启动脚本、离线/集成测试、独立合成 JSON、架构和运行文档、经审查的真实公开示例截图、许可证与逐文件清单。原课程源码思想以 SOURCE_MAP 说明，原文件及未明确可再分发材料不复制。

不公开：DOCX、ZIP、课程 SQL、原标注全文、原前端包、安装器、缓存、Conda/venv、模型权重、数据库、日志、密钥、个人目录和个人字段。data/private、reports/private、artifacts、.runtime 均忽略。models 与 materials_private 只保留说明或空占位。

`check_public_boundary.py` 检查候选、暂存区和可达 Git 历史；匹配输出只含规则与路径，不显示密钥。启发式扫描有漏检可能，必须结合许可与文件审阅。历史发现真实泄露不能用隐藏文件或删除当前文件掩盖。

`publish_manifest.json` 列出每个文件和 SHA-256；两个控制 JSON 自身使用 null 避免递归。`verify_manifest.py` 校验文件集合与摘要，`validate_release.py --run` 执行当前代码和依赖门禁。READY 仅指源码发布检查通过，不表示完整训练、在线模型或网站部署已完成。
