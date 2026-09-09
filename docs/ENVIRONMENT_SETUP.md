# 环境配置与隔离

先在当前机器执行 `scripts/check_environment.py`，实际报告操作系统、磁盘、解释器、GPU/驱动、Java、MySQL、Neo4j、Conda、Git 和端口。工具存在不表示版本匹配或服务已启动。所有命令绑定解释器并打印 sys.executable；当前验证使用 Windows x64、Python 3.12、CPU PyTorch。

|用途|解释器/运行位置|默认端口|
|---|---|---|
|图与聊天|.venv-public/Scripts/python.exe|API 8012；Neo4j HTTP 7476、Bolt 7689|
|训练|.conda/graph/python.exe|前台任务，无端口|
|人工标注|.conda/label-studio/python.exe|8082|
|ML Backend|.conda/ml-backend/python.exe|9092|
|原生 MySQL|.runtime 中固定二进制、专属数据目录|3308|

本次发布在另一组空闲端口 8013/7477/7690/3310 验证；原工程端口及环境保留。端口由首次配置写入 runtime.json，后续脚本读取，不必占用用户其他服务。

配置优先级：进程环境 > 仓库 .env > artifacts/local/runtime.json > 默认。密码用 SecretStr，diagnostics 仅返回配置是否存在；凭据写忽略文件，不放命令行。外部 Neo4j URI、嵌入账号密码的 URI 不接受。

默认 DEMO_MODE=true。开启 online 配置仍需本地授权、合成数据范围与预算，不能仅凭前端参数启动付费请求。envs/locks/public 是实际主验证环境锁；标注与模型服务分开安装、审计和验收，不继承主环境扫描结论。

CPU 安装使用 PyTorch 官方 CPU index。GPU 训练须先核对本机与官方支持矩阵，不盲装 cu128，不默认安装 WSL。Docker 是另一路线，本修订未执行容器运行，不能与原生服务共占端口。
