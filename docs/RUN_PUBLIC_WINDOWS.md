# 独立公开示例：Windows 操作

适用 Windows x64、Python 3.12。使用 PowerShell，保留至少 12 GiB 空间。进入克隆所得仓库目录后执行下列命令；`$PWD` 表示当前目录。不要在课程私有运行目录执行 `sample_demo configure`，脚本会拒绝覆盖。

终端 1，首次安装（仅运行一次）。已安装 Python 3.12 时可用 `py -3.12` 查到真实路径；脚本检查版本并打印实际解释器。未安装 Python 时先从 python.org 安装 3.12。

```powershell
$basePython = (py -3.12 -c "import sys; print(sys.executable)")
& ./scripts/public_bootstrap.ps1 -Python $basePython
```

若当前终端禁止脚本，另开仅本进程放行的终端 `powershell.exe -NoProfile -ExecutionPolicy Bypass`，不修改全局策略。成功最后显示 `Installation complete`，环境为本目录 `.venv-public/Scripts/python.exe`。

终端 1，首次建图与索引：

```powershell
$env:PYTHONUTF8='1'
& ./.venv-public/Scripts/python.exe scripts/services.py start neo4j
& ./.venv-public/Scripts/python.exe scripts/sample_demo.py secure
& ./.venv-public/Scripts/python.exe scripts/sample_demo.py build
& ./.venv-public/Scripts/python.exe scripts/create_indexes.py
& ./.venv-public/Scripts/python.exe scripts/serving_mode.py serve
& ./.venv-public/Scripts/python.exe scripts/services.py start api
Invoke-RestMethod http://127.0.0.1:8012/health/ready
```

服务启动命令返回 `started-not-yet-ready` 仅表示进程启动。建图与索引须分别输出 `passed`；健康检查返回 `ready` 后打开 [聊天页面](http://127.0.0.1:8012)。首次 API 启动可能需数十秒，健康检查连接失败时等待后重试。Neo4j 使用 7476/7689，与私有项目分离。

日常启动不再安装、建图、重建索引：

```powershell
& ./.venv-public/Scripts/python.exe scripts/services.py start neo4j
& ./.venv-public/Scripts/python.exe scripts/services.py start api
Invoke-RestMethod http://127.0.0.1:8012/health/ready
```

停止命令（同一目录）：

```powershell
& ./.venv-public/Scripts/python.exe scripts/services.py stop api
& ./.venv-public/Scripts/python.exe scripts/services.py stop neo4j
```

Neo4j 正常停止会输出 `neo4j-bootstrapper-stop`，不要直接结束 Java 进程。冲突端口会报错，脚本不会终止已有软件。

终端 2，验证：

```powershell
& ./.venv-public/Scripts/python.exe -m pytest tests/unit -q
& ./.venv-public/Scripts/python.exe scripts/generate_sample.py --check
& ./.venv-public/Scripts/python.exe scripts/public_verify.py
```

未安装独立 ML SDK 时，两个 ML 测试模块显示跳过；这不是在线预标注成功。公开示例没有 BERT 训练集或 checkpoint，不运行训练替代品。完整私有课程的三环境、标注和训练命令由拥有资料的学习者在其本地交付文档中使用。

失败排查：先看 HTTP 状态和 JSON 类型，再看 `reports/private/api.stderr.log`、`neo4j.stderr.log`；`health/ready` 的 `unavailable` 不能当作服务就绪。所有日志、认证文件、运行时和模型缓存都在本目录的忽略区域。

`sample_demo build` 由已跟踪脚本生成本地 `configs/approved-aliases.json`，它是独立样例的派生配置并被 Git 忽略；从空目录按上述步骤运行会自动重建，无需从私人目录复制文件。
