# 评测口径

功能合同测试不计算模型质量。公开合成数据用于图导入、消歧和证据回答；不将三件商品上的通过率称为检索召回率。发布门禁状态见 release_validation.json。

正式 NER 评测需要先冻结按原文 hash 分组的 train/validation/test，仅验证集选 checkpoint。独立 test 输出精确原文实体跨度 P/R/F1、字符 BIO accuracy 和逐条预测。当前正式训练与该评测均未运行，旧私有模型分数不继承到当前修订。

随机微型模型的两步 smoke 只验证训练接口、safetensors 保存和分词器重新加载。实际图集成、HTTP、真实浏览器和模拟故障分别计数；无模型和无数据库时不得回退关键词冒充对应验证。
