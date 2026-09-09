# 故障排查

|现象|先检查|处理|
|---|---|---|
|找不到 Python|命令中的绝对路径、sys.executable|使用已有3.12路径，不能改用裸pip|
|端口占用|scripts/check_environment.py；进程来源|不结束他人进程；检查本项目注册记录|
|started-not-yet-ready|/health/ready状态码和JSON|等待启动；若持续503读本地stderr|
|API静态页正常却无法聊天|/api/status的Neo4j/embedding|确认10个ONLINE索引、BGE缓存、只读serve模式|
|导入拒绝|graph_sync_report/端点错误|保留原件，审查异常；不造缺失节点|
|同名商品总要求澄清|候选ID、类型、名称|这是预期行为，选择具体商品|
|缺best_model|完整bundle和来源文件|运行真实训练；基础BERT不能冒充|
|ML Backend 503 inference_blocked|授权和key是否配置|继续人工标注；不返回伪预测|
|MySQL unavailable|配置端口、凭据存在、SELECT权限|初始化专属schema；不打印密码|
|Docker named pipe不存在|docker version|引擎未运行，标未运行；不默认安装WSL|
|安全审计失败|release_validation中的包和报告ID|核对上游修复并隔离验证，不忽略报告|
|重启后旧澄清令牌失效|服务进程是否重启|重新提问，令牌不持久化|

日志在 reports/private，包含明确的 stdout/stderr、测试输出、时间和解释器。问题排查应按请求地址→状态码→响应类型→响应体→后端日志顺序；不要把未运行写成失败或通过。只分享脱敏错误类型与最小合成输入。
