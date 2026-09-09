# 实测依赖锁

public-pip-win64.txt 与 development-pip-win64.txt 记录此次 Windows Python 3.12 CPU 验证环境的完整第三方包集合，包含训练和开发检查工具；不是最小推理依赖。它们没有本机绝对路径和 editable 源码路径，源码另用 `-e .` 安装。先从 PyTorch 官方 CPU index 安装 torch==2.14.0，再安装锁。

security-requirements.txt 对同一集合审计：CPU 构建 2.14.0+cpu 映射到上游 torch 2.14.0，避免 pip-audit 因 PyPI 没有 +cpu 构建而跳过；本仓库自身由源码审查与测试覆盖。`--no-deps --disable-pip` 只避免重新解析/下载，锁已包括传递依赖，不忽略漏洞或包。主环境的固定直接依赖见 pyproject.toml 与 envs/public-requirements.in。

当前扫描结论见 release_validation.json。每次变更应在独立环境实际安装、运行、重新锁定和审计；不要把 Windows 锁当作所有平台均已验证的证明。Label Studio 与 ML Backend 的隔离环境单独验收，不混入图环境。
