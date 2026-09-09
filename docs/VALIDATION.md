# 发布验证记录

下表由本次本机检查结果整理。完整日志只保存在 reports/private，公开 release_validation.json 记录状态和文件摘要。检查由 Codex 在本机执行，不代表用户已经在独立终端重现或掌握代码。

|检查|状态|本地证据/公开摘要|
|---|---|---|
|required_files|PASS|release_validation.json|
|public_boundary|PASS|release_validation.json|
|ruff|PASS|reports\private\release-checks\ruff.log|
|mypy|PASS|reports\private\release-checks\mypy.log|
|compile|PASS|reports\private\release-checks\compile.log|
|unit_and_api_mock|PASS|reports\private\release-checks\unit_and_api_mock.log|
|pip_check|PASS|reports\private\release-checks\pip_check.log|
|dependency_audit|PASS|reports\private\release-checks\dependency_audit.log|
|real_database_integration|PASS|reports/private/github-real-integration.xml|
|independent_ml_sdk_mock|PASS|reports/private/github-ml-sdk.xml|
|synthetic_training_contract|PASS|reports/private/transformers-contract.xml|
|browser_real_and_fault_injection|PASS|reports/private/browser-e2e.json|
|native_restart|PASS|reports/private/public-verification.json|
|clean_source_installation|PASS|reports/private/github-clean-validation.json|

单元/API mock 为 90 项通过、2 个独立 SDK 模块跳过；SDK 单独运行时另行记录。真实数据库 5 项通过，索引 10 个 ONLINE 且重复编码为 0；真实 HTTP 15 个请求及重启前后 25/31 图计数核对通过。浏览器 2 项真实请求检查、6 项明确故障注入分别记录。

随机微型 BERT 的 2-step 训练、保存、重载合同测试通过；正式 BERT 训练、独立质量 F1、真实 AI 预标注、DeepSeek 在线调用、Label Studio 新环境人工流程和 Docker 运行均 NOT_RUN。未运行项不会回退规则或基础模型伪装成功。

依赖扫描覆盖 123 个第三方分发包，CPU torch 映射上游版本；没有跳过包或忽略漏洞。FastAPI 测试的上游弃用提示保留在日志，未吞掉失败。

GitHub Actions 的状态看对应远端提交的实际运行，本机 JSON 不预测远端结果。源码发布和公网部署分开；本仓库未部署网站。发布门禁 READY 仅适用于审核范围内源码与独立样例。
