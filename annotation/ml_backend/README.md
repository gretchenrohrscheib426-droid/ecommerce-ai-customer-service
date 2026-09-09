# 独立 ML Backend

安装与人工标注流程见 [NER_PIPELINE](../../docs/NER_PIPELINE.md)。此目录运行在 `.conda/ml-backend`，与 Label Studio 和图环境隔离；SDK 固定为上游提交。`_wsgi.py` 提供服务入口，`model.py` 实现预测协议与原文跨度校验。

默认 ML_MODE=blocked，未授权真实模型调用时返回明确的 503 inference_blocked。协议 mock 成功不是 AI 预标注成功；已有标注 JSON 也不能代替服务验收。原始请求、密钥与标注全文不写公开日志。

创建独立环境后，用该环境解释器运行 `scripts/install_ml_backend.py`：先安装本文件夹 requirements.txt 中的固定依赖，再安装固定上游源码并执行 pip check。上游原始 requirements 引用未固定的 Git SDK，因而这里显式固定 SDK 2.1.1；源码包的 --no-deps 只禁止重新解析这条 Git 依赖，全部声明依赖已单独安装和检查。两个协议测试应在该环境执行，真实在线模型状态仍单独验收。

安装器同时安装当前仓库及其轻量基础依赖，使独立后端可导入共享跨度校验代码；不安装图检索或训练 extras。新建 SDK 环境实测 7 项协议测试通过，模型提供方为明确 mock，不代表真实 AI 预标注通过。
