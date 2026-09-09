# 独立演示问题

sample_questions.json 有 10 个实际 HTTP 验证过的输入，expected_responses.json 列出稳定的业务状态。具体 trace_id、耗时、澄清令牌每次不同，不硬编码成固定回答。公开数据标为 Synthetic Demo Data；价格与商品均为虚构。

模糊查询通过 BGE/全文候选后需要澄清；精确名称与批准别名可提前命中。示例集是功能回归，不是独立检索 benchmark。Tag 人工合成，正式训练和在线 DeepSeek 的未运行状态与这些问题的离线成功分开。
