# 模型目录边界

此目录仅作模型约定说明，不提交任何权重。基础模型和 BGE 放在 artifacts/local/models；训练输出放 artifacts/local/<run-name>/best_model，全部被 Git 忽略。

本公开修订没有真实 best_model，训练评估状态 BLOCKED_MODEL_NOT_TRAINED。Predictor 要求完整模型、分词器、配置与训练来源，不会静默回退到基础 BERT 或关键词规则。下载的基础模型不算训练结果。参考 docs/TRAINING_GUIDE.md。
