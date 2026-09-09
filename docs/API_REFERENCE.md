# 本地 API

私有课程使用 8001，独立公开示例使用 8012。只监听 127.0.0.1。

`GET /` 返回静态页面；`GET /health/live` 仅说明进程存在；`GET /health/ready` 检查所选聊天依赖，未就绪返回 503。Label Studio 和 ML Backend 是按需组件，不是聊天就绪前提。

`POST /api/chat`，JSON：`{"message":"青岚示例品牌有哪些商品"}`。message 必须为非空字符串，最多 500 字；未知字段拒绝。响应保留 `message`，另有 `status`、`evidence`、`trace_id`、`generation`、`steps`。

status 可为 ok、clarify、no_match、no_results、unsupported、invalid_request、online_unavailable。依赖故障 HTTP 503、并发超限 429、总响应等待超时 504、字段不合法 422、超大请求体 413、跨源 POST 403。没有把技术故障转成“没有商品”。

澄清响应含 candidates 和 clarification_token。再次提交必须同时提供原 message、候选 canonical_id 作为 choice、原令牌；令牌绑定问题与候选，消费一次，300 秒失效。原问题变化需新建澄清，不能用前端自报实体绕过。

没有 `/api/cypher`，没有 query/raw/database 管理参数。只允许源码中的 9 条准确模板，参数实体 ID 为正整数且禁止 bool，limit 1–20，固定目标库和路径长度。BGE 检索过程仅由固定模板调用。

在线模式为可选依赖，私有 `artifacts/local/online_authorization.json` 需明确模型名、allowed_dataset、chat_enabled、annotation_enabled、max_chat_calls、max_annotation_calls；密钥仅在后端环境变量 DEEPSEEK_API_KEY，开关 ECOMMERCE_ONLINE=1。当前没有该授权文件，不提供自动启用付费调用命令。safe-demo 在线做计划与证据行选择；course-reference 额外生成并逐字验证已批准模板与已确认 ID。最终商品字段始终从真实查询行格式化，不让模型补造价格。
