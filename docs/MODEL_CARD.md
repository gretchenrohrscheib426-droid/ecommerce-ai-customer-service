# 模型说明

检索使用 BAAI/bge-small-zh-v1.5，固定 revision 7999e1d3359715c523056ef9478215996d62a620、512 维、归一化 cosine。下载来源与每个文件摘要保存在本地 download_provenance.json；权重不进 Git。模型许可见 THIRD_PARTY_NOTICES。

BERT TAG 使用 google-bert/bert-base-chinese 作为微调起点。下载基础权重不构成训练成果。公开版本未完成正式训练，未发布 best_model，不报告 F1；随机微型 BERT 的 2-step API 合同测试只检查 train、save、reload 与分词器对齐。

公开图中的 Tag 是人工合成 fixture。商品标题训练后的模型也不能未经评估直接声称对商品描述泛化。必须使用独立人工 gold 测试集评估精确原文跨度，保留逐条预测与错误分析。
