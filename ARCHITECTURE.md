# 架构与数据边界

运行分为课程私有复现与独立公开示例。两者数据命名空间、端口、凭据和模型目录分离。公开页面以合成示例运行，默认没有在线 LLM。

```mermaid
flowchart LR
  Title[商品标题] --> LS[Label Studio 人工标注]
  ML[独立 ML Backend] --> LS
  LS --> Export[人工检查与导出]
  Export --> Check[跨度校验与冻结切分]
  Check --> BERT[BERT TAG 训练 / 独立测试]
  BERT --> Bundle[模型 + 分词器 + 配置 + 来源]
```

```mermaid
flowchart LR
  M[MySQL 12张业务表] --> V[主键 / 端点 / 重复检查]
  V -->|合法关系| G[Neo4j 业务ID节点]
  V -->|异常| Q[保留原记录的隔离报告]
  D[商品描述] --> N[真实微调模型]
  N --> T[含跨度和来源的Tag]
  T -->|SPU Have Tag| G
```

```mermaid
flowchart LR
  Q[用户问题] --> P[规则或授权的DeepSeek解析]
  P --> H[BGE向量 + 全文 + RRF]
  H --> A{实体唯一且已确认}
  A -->|否| C[一次性澄清 token]
  C --> A
  A -->|是| V[受控Cypher模板 + 参数]
  V --> R[实际结果]
  R --> F[本地事实格式化 / 可选证据选择]
  F --> W[回答 + 来源 + trace_id]
```

```mermaid
sequenceDiagram
  participant Browser as 静态页面
  participant API as FastAPI
  participant Agent as 有界工作流
  participant Graph as Neo4j
  Browser->>API: POST /api/chat
  API->>API: 请求体/来源/并发校验
  API->>Agent: Question
  Agent->>Graph: 候选检索与固定只读查询
  Graph-->>Agent: 实际字段
  Agent-->>API: Answer及证据
  API-->>Browser: JSON
  Browser->>Browser: textContent显示
```

```mermaid
flowchart TB
  Private[课程私有工作区: 原件/SQL/标注/权重] -.不进入发布清单.-> Boundary[白名单与历史扫描]
  Public[独立实现 + 合成JSON + 文档 + 测试] --> Boundary
  Boundary --> Review[当前代码发布门禁]
  Review --> Approval[后续另行确认发布目标]
```

Neo4j 使用固定 neo4j 数据库和数据集标记。服务模式检查实际只读状态；构建模式才允许同步。公共关系写入在事务中验证两端，失败回滚；运行接口不提供写操作。HTTP 同步工作放入线程，最多两个并发工作，请求与模型调用有超时。澄清存于单进程内存，有 TTL 和一次性消费，不是分布式会话系统。
