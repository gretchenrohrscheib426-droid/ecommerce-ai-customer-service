# BGE、全文与实体对齐

graph/indexes.py 使用固定 BAAI/bge-small-zh-v1.5 revision，实际输出 512 维。对 SPU、品牌、三层分类分别建立向量与全文索引，共 10 个；建索引时核对标签、字段、维度、cosine、分析器和 ONLINE 状态。未变化的文本和模型摘要不会重算向量。

retrieval/search.py 分别取向量与全文候选，使用 RRF（按候选排名合并）形成列表。RRF score 是融合排名分数，不是概率，也不是直接 cosine。每个候选保留 canonical_id、name、label、metadata、两路来源。hybrid.py 提供类型化候选，entity_alignment.py 返回 resolved/ambiguous/not_found。

精确唯一名称或经过明确登记的唯一别名可对齐；同名、低分和模糊命中需要用户选择，不能直接把 top1 当实体。阈值默认 0.85，作用于候选筛选，不是无需澄清的正确率保证。entity metadata 不是只有 page_content 的空壳。

```powershell
& .\.venv-public\Scripts\python.exe scripts/create_indexes.py
$env:ECOMMERCE_PUBLIC_INTEGRATION='1'
& .\.venv-public\Scripts\python.exe -m pytest tests/integration/test_hybrid_retrieval.py -q
```

当前公开真实检索测试验证合成品牌的向量/全文来源与身份，小样例不能宣称大规模 recall。没有独立模糊查询 gold 集时不报告召回率。
