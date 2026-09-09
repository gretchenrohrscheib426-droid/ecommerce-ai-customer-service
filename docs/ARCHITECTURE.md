# 实际模块关系

```mermaid
flowchart TD
  LS[Label Studio 8082] -->|任务协议| ML[独立 ML Backend 9092]
  ML -.授权后 DeepSeek 预标注.-> LS
  LS --> EX[JSON-MIN 校验 / UTF-16 转字符坐标]
  EX --> PR[process 冻结切分与 offset 对齐]
  PR --> TR[train BERT TAG]
  TR --> EV[evaluate / Predictor]
  SQL[专属 MySQL 的 12 表] --> VP[graph_plan 外键校验]
  VP --> SY[sync_plan 幂等构图]
  EV --> TAG[sync_tags 来源跨度]
  SY --> N[专属 Neo4j]
  TAG --> N
  N --> IX[五类实体的全文 + 512 维向量索引]
  UI[静态页面] --> API[FastAPI]
  API --> CS[ChatService 有限状态]
  CS --> RE[Retriever 与实体澄清]
  IX --> RE
  RE --> CQ[固定 Cypher 与参数]
  CQ --> N
  N --> AN[实际字段回答与 evidence]
  AN --> UI
```

课程私有实例与独立公开示例使用不同数据目录和端口。公开样例直接由 12 表形状的独立 JSON 建图，人工 Tag 夹具明确标注；公开版本已从专属 MySQL 实际同步；正式训练与在线调用未验证，不继承旧版成绩。

`Settings` 只解析配置；`schema.py` 定义输入/计划；`Predictor` 做已训练模型推理；`sync_plan` 对应 TableSynchronizer；`sync_tags` 对应 TextSynchronizer；`create_indexes` 构建检查索引；`Retriever` 返回结构化 metadata 并拒绝擅自选择模糊首项；`ChatService` 控制最多六个步骤。

原课程依赖 LangChain 的部分流程在本实现中用类型 schema、官方驱动和 httpx 显式重写，保留业务链路并缩小动态查询能力；安装了集成依赖不等于实际采用了其 Agent。未使用 LangGraph、CrewAI、MCP、多智能体或自主工具选择。
