# BERT TAG 训练和独立测试

公开示例缺少完整训练语料及真实 best_model。当前修订的正式训练状态 BLOCKED_MODEL_NOT_TRAINED；基础 BERT 下载不是训练成功。本修订不报告正式训练 F1。

在独立训练环境（envs/graph.yml）执行，先打印真实解释器。GPU 安装须按本机检测另行选择；下列默认 CPU 安装能复现代码但可能耗时。现存训练模型不要覆盖。

```powershell
# 在本仓库根目录执行
$condaExe = (Get-Command conda -ErrorAction Stop).Source
& $condaExe env create --prefix "$PWD\.conda\graph" -f envs/graph.yml
& .\.conda\graph\python.exe -c "import sys; print(sys.executable)"
& .\.conda\graph\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.0
& .\.conda\graph\python.exe -m pip install -e '.[training,retrieval]'
& .\.conda\graph\python.exe scripts/download_models.py
& .\.conda\graph\python.exe -m ecommerce_graph_agent prepare-ner --source data/ner/raw/reviewed.json
& .\.conda\graph\python.exe -m ecommerce_graph_agent train-ner --run-type smoke --run-name ner-smoke-v2
& .\.conda\graph\python.exe -m ecommerce_graph_agent train-ner --run-type full --run-name ner-full-v2
& .\.conda\graph\python.exe -m ecommerce_graph_agent.models.ner.eval --model artifacts/local/ner-full-v2/best_model --split-dir data/private/ner-v1 --output artifacts/metrics/ner_test_metrics-v2.json
```

这些是可执行入口；当前修订没有重新下载/训练来制造新成绩。语料应由有权使用的人工导出准备，公开 3 条 fixture 只做格式回归。prepare-ner 输出若已存在会拒绝覆盖；新版本应使用独立工作区或明确创建新的派生路径，不删除冻结测试集。

训练先用字符列表调用 fast tokenizer 的 is_split_into_words=True，取 word_ids，把 token 的局部 offset 恢复到原始字符。特殊 token 和 pad 为 -100，完整单词分裂后的子 token 按原文跨度产生 B/I/O。空格没有 token 时仍检查实体覆盖与原文恢复，不能仅用 tokens 拼字符串。过长文本明确拒绝，不静默截断漏实体。

smoke 只取少量训练/验证数据，验证流程而非模型质量；full 默认 10 epoch、固定 seed，验证集选最优。best_model 保存 model.safetensors、config.json、分词器、training_provenance.json，并记录模型摘要及对齐策略。预测只加载完整微调 bundle；输出 original_text、token_offsets、entities 和 model_sha256。

独立 eval 检查冻结 test 文件摘要，保存精确原文跨度 P/R/F1、字符级 BIO accuracy 和逐条预测。Accuracy 的单位不是 token，报告中明确标注。旧 evaluate.py 保留用于旧私有产物对照。

停止训练在该前台终端 Ctrl+C；未完成的输出不能改名为正式 best_model，也不要接到服务。再次训练选新 run-name。
