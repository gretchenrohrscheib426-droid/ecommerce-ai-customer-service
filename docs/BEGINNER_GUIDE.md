# 按课程五章读本工程

这是学习路线，不是用户已掌握记录。先读一个函数，说明输入、输出和失败行为，再继续。

1. 环境与图基础：读 `src/ecommerce_graph_agent/config.py` 的 `Settings.load`。输入是项目根目录、可选环境变量和本地运行配置；输出是明确端口和模式。`python -m ecommerce_graph_agent doctor` 应打印实际解释器与“密钥是否存在”，不打印密钥值。SPU 表示一组共同产品信息，SKU 表示可销售的具体规格；两者由业务 ID 区分，名字不是主键。
2. 数据标注：读 `annotation/ml_backend/model.py` 的 `predict` 与 `models/ner/process.py` 的 `validate_record`。输入标题和原文区间，输出 Label Studio 预测协议或校验后的区间。Label Studio 用 UTF-16 索引，Python 用 Unicode 字符位置，emoji 会让两者不同。先在独立样例选 TAG，Submit 和 JSON-MIN 导出，再检查半开区间 `[start,end)` 是否精确还原文字。重叠必须人工复核。
3. BERT：读 `process.py` 的 tokenizer offset 对齐、`train.py` 的 `train`，然后读 `predict.py` 的 `Predictor.predict`。token 是模型分词后的单位；offset 是其在原文的位置。B/I/O 分别表示实体开头、内部和非实体。训练集负责更新参数，验证集选 checkpoint，测试集最后评估一次。Predictor 只加载真实 full bundle，不会找不到模型时改用基础 BERT。运行命令见 RUN_WINDOWS；输出跨度可以逐字检查。
4. 图同步：课程的 TableSynchronizer 在本实现对应 `datasync/validate.py` 的 `graph_plan` 和 `datasync/sync.py` 的 `sync_plan`；TextSynchronizer 对应 `sync_tags`。前者输入 12 表，先隔离异常关系，再按稳定 ID 写图并对账；后者输入真实模型跨度，保存原文哈希、来源字段、模型版本，并按商品描述范围更新。导入数和预期数必须分别记录，重复执行不应增加节点。
5. 问答应用：依次读 `retrieval/indexes.py`、`retrieval/search.py`、`qa/schema.py`、`qa/cypher.py`、`qa/service.py` 和 `web/app.py`。本工程文件名是单数 `schema.py`。索引帮助找到候选；实体对齐决定候选是否唯一；ChatService 管理解析、澄清和查询；Cypher 模板限定可读的字段和关系；FastAPI 只负责 HTTP 接口。先问完整品牌，再问同名商品，观察澄清令牌如何绑定问题。

常见错误：基础模型目录不是训练结果；状态 alive 不是依赖 ready；图的 READ 路由不是数据库授权；上架标记不是库存；标题测试成绩不能证明描述抽取准确率；公开人工 Tag 不属于模型预测。

建议下一条学习提交物：用自己的话解释 `Predictor.predict` 如何从 tokenizer 的 offset 回到原文，以及为什么 id=677 必须被隔离。附一条独立示例的 start/end/text；先不给标准答案，也不以“看懂了”判断掌握。
