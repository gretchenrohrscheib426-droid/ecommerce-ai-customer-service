# Windows 从零运行

所有终端均使用 Windows PowerShell。先打开准备存放项目、空间充足的目录；下面 clone 会创建新的子目录。已有克隆时直接用资源管理器进入该目录并打开终端。不要在私有课程目录覆盖安装。

## 终端 1：首次安装与聊天

```powershell
git clone https://github.com/gretchenrohrscheib426-droid/ecommerce-ai-customer-service.git
Set-Location ecommerce-ai-customer-service
$projectRoot = (Get-Location).Path
$basePython = (py -3.12 -c "import sys; print(sys.executable)").Trim()
& $basePython -X utf8 scripts/check_environment.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/public_bootstrap.ps1 -Python $basePython
```

`py` 找不到时，执行 `Get-Command python`，把实际 Python 3.12 的完整路径赋给 `$basePython`。预检记录操作系统、磁盘、解释器、GPU/驱动、Java、Conda、Git 与端口；不要把“命令存在”当成服务可用。预检不修复系统。安装脚本将打印两个 sys.executable：基础解释器和新 `.venv-public` 解释器。

安装仅落在当前仓库 `.venv-public`、`.runtime`、`.cache` 与 `artifacts/local`。已有环境会复用，若要测试全新安装请重新克隆到新目录。安装脚本默认 CPU，不需要显卡，不更换系统 Python。下载失败的日志/摘要不构成安装成功。

```powershell
& .\.venv-public\Scripts\python.exe -c "import sys; print(sys.executable)"
& .\.venv-public\Scripts\python.exe scripts/services.py start neo4j
& .\.venv-public\Scripts\python.exe scripts/sample_demo.py secure
& .\.venv-public\Scripts\python.exe scripts/sample_demo.py build
& .\.venv-public\Scripts\python.exe scripts/create_indexes.py
& .\.venv-public\Scripts\python.exe scripts/serving_mode.py serve
& .\.venv-public\Scripts\python.exe scripts/services.py start api
Invoke-RestMethod http://127.0.0.1:8012/health/ready
```

`build` 打印 passed 和实际节点/关系计数；`create_indexes` 必须完成 10 个向量/全文索引；`serve` 必须显示 read-only 与 denied。健康接口成功后打开 http://127.0.0.1:8012，问“随行水杯价格”。应该出现实际价格、未上架状态与来源。图写入失败时不要跳过错误直接启动。

端口默认 Neo4j Bolt 7689、HTTP 7476、聊天 8012；如果被占用，安装前检查占用程序。另选端口须在**首次配置前**使用 `sample_demo.py configure --bolt-port 7690 --http-port 7477 --api-port 8013`，并让安装脚本传入相同端口。已有配置不允许原地改成另一组；使用新的克隆。所有后续验证读取 runtime.json；浏览器地址也改用新 api-port。

## 日常使用、停止和重启

新 PowerShell 终端仍先进入仓库根目录，再执行：

```powershell
& .\.venv-public\Scripts\python.exe -c "import sys; print(sys.executable)"
& .\.venv-public\Scripts\python.exe scripts/run_demo.py start
Invoke-RestMethod http://127.0.0.1:8012/health/ready
& .\.venv-public\Scripts\python.exe scripts/public_verify.py --restart
& .\.venv-public\Scripts\python.exe scripts/run_demo.py stop
```

最后一条停止本仓库记录的 API 和 Neo4j；终端关闭不会自动停止后台服务。重启验证比较数据库计数与索引，重新发送实际 HTTP 问题，不重新安装或导入。日志在 reports/private，进程记录在 artifacts/local/processes.json；不使用全局 taskkill。

## 终端 2：标注；终端 3：训练

标注与训练不需要和聊天同时运行。标注环境、模型后端环境、图与训练环境互相隔离，完整命令分别见 [NER_PIPELINE](NER_PIPELINE.md)、[TRAINING_GUIDE](TRAINING_GUIDE.md)。服务可启动与真实 AI 预测成功是两个验收项。没有 API key 可继续人工导出、校验与离线测试。

完整 MySQL → Neo4j 路线见 [DATA_PIPELINE](DATA_PIPELINE.md)。普通聊天启动不依赖重新导入 MySQL。
