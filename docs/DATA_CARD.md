# 公开数据卡

来源为本仓库独立编写的 Synthetic Demo Data，见 scripts/generate_sample.py 与 generate_demo_data.py。所有商品、品牌、价格和属性为虚构，目的为可重复验证，不是现实商品事实。

12 个表，3 个 SPU、3 个 SKU、2 个品牌；两个 SPU 同名但 ID 和品牌不同。生成器确定性运行，`--check` 校验已提交 JSON 与生成结果一致。公开 JSON 中没有账号、地址、订单或用户画像。

NER fixture 仅供格式/跨度回归；不是正式训练语料。图中 4 个人工合成 Tag 明确标注 manual-fixture 来源，不冒充 BERT 抽取。图实际计数与重复同步检查见 release_validation.json 对应记录。

课程数据的再分发许可未确认，因此 DOCX、ZIP、SQL、完整标注和原图保持私有。缺失端点与重叠标注通过独立非法输入测试拒绝路径；本仓库不公开原始问题记录全文。
