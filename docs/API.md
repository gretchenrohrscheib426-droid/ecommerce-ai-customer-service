# HTTP 接口

服务地址默认 http://127.0.0.1:8012。FastAPI 提供 /docs；静态页面与 API 同源。

|方法与路径|意义|
|---|---|
|GET /|静态聊天页面|
|GET /health|应用进程存活|
|GET /api/status|app/mysql/neo4j/llm/ner_model/embedding 各自真实状态|
|GET /health/live|兼容存活检查|
|GET /health/ready|数据库、索引、模型加载就绪；失败 HTTP 503|
|POST /api/chat|受控问题与澄清选择|

```powershell
$body = @{message='随行水杯价格'} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8012/api/chat -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
```

请求 message 为 1–500 字符，空白拒绝，额外字段拒绝。澄清时原 message 配合 clarification_token 与 choice，不可跨问题复用。请求体最多 8192 字节，同源/本地主机检查；HTTP 422 表示 schema 错误，403 来源被拒，503 依赖不可用或并发容量用尽。

回答包含 message、status、trace_id、grounded、evidence、candidates、clarification_token、generation、steps。grounded=true 仅表示实际图结果支持当前回答，不是模型正确率认证。状态无结果或unsupported不返回虚构事实。generation=local-result-formatting 是本地模板回答，不能写成 DeepSeek 调用成功。

api/status 的 configured_not_probed 只表示配置齐全，不是在线健康；ner_model=bundle_present_not_probed 只表示文件存在，不是精度验收。mysql=not_configured 与 unavailable 有区别。页面显示 Synthetic Demo Data 及这些状态。
