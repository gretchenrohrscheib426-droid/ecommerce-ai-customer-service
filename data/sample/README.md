# Synthetic Demo Data

公开数据完全虚构、独立编写。business.json 是 12 张业务表；products.json 是便于阅读的商品视图；ner_sample.json 是 3 条人工 TAG 格式样例；annotation_tasks.json 是 Label Studio 导入任务。

3 个商品、3 个 SKU、2 个品牌，包含同名异品牌的“轻旅背包”和“随行水杯”。价格为固定测试值。4 个 Tag 仅为人工 fixture，不是 AI 标注或 BERT 预测。样例规模不足以训练/评估通用 NER，禁止宣称真实商业数据和模型质量。

重新生成：.venv-public/Scripts/python.exe scripts/generate_demo_data.py；只检查：追加 --check。
