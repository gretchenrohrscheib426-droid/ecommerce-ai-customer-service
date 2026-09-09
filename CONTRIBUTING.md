# 贡献指南

先阅读 AGENTS.md、SOURCE_MAP.md 和 PUBLIC_PRIVATE_BOUNDARY。使用 Python 3.12 的独立环境，不修改他人数据库、课程原件或既有 Conda 环境。

```powershell
& .\.venv-public\Scripts\python.exe -m pip install -r requirements-dev.txt
& .\.venv-public\Scripts\python.exe -m ruff check src tests scripts annotation
& .\.venv-public\Scripts\python.exe -m mypy src/ecommerce_graph_agent
& .\.venv-public\Scripts\python.exe -m pytest tests/unit tests/e2e/test_api.py -q
& .\.venv-public\Scripts\python.exe scripts/check_public_boundary.py
```

数据库集成需要显式 ECOMMERCE_PUBLIC_INTEGRATION=1；写入测试还需 ECOMMERCE_GRAPH_WRITABLE=1，并只能指向专属合成库。不要为使测试通过而吞异常、删断言或把集成失败改成无条件 skip。

改动说明应写清触发场景、行为变化、来源类型、测试命令与实际结果。新依赖需说明作用、固定版本、来源许可和漏洞审查；避免仅为展示堆叠框架。PR 中不得包含课程文件、SQL、真实标注、模型缓存或密钥。按模板区分 mock 与真实调用。
