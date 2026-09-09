# 标注服务与 NER 数据

NER 是命名实体识别：这里从原文选出商品特征 TAG。Label Studio 提供人工选区，独立 ML Backend 遵循其预测协议；已有标注文件不能代替这两个服务的验收。

公开环境安装命令，终端 2 在仓库根目录执行。先通过 Get-Command conda 获得实际 Conda 路径，用绝对路径替换下例变量，禁止覆盖已存在的 prefix：

```powershell
$condaExe = (Get-Command conda -ErrorAction Stop).Source
& $condaExe env create --prefix "$PWD\.conda\label-studio" -f envs/label-studio.yml
& $condaExe env create --prefix "$PWD\.conda\ml-backend" -f envs/ml-backend.yml
& .\.conda\label-studio\python.exe -c "import sys; print(sys.executable)"
& .\.conda\ml-backend\python.exe -c "import sys; print(sys.executable)"
& .\.conda\ml-backend\python.exe scripts/install_ml_backend.py
& .\.venv-public\Scripts\python.exe scripts/configure_annotation.py
& .\.venv-public\Scripts\python.exe scripts/services.py start label-studio
& .\.venv-public\Scripts\python.exe scripts/services.py start ml-backend
```

configure_annotation 提示输入本地密码（隐藏输入），保存在忽略的凭据文件；已有配置不改写。打开 http://127.0.0.1:8082，用 learner@example.invalid 与自己刚输入的密码登录，创建项目，将 configs/label_studio.xml 放入 Labeling Interface，导入 data/sample/annotation_tasks.json。设置模型 URL 为 http://127.0.0.1:9092。

选择 TAG、拖选实际特征、Submit，人工检查后从 Export 导出 JSON-MIN 到 data/ner/raw/reviewed.json。不能把“浏览器自动提交测试”称为用户已经学会标注。这两个公开环境的真实服务验收须单独记录；不能用图环境的测试替代。

没有明确调用授权及 key 时，预标注返回 503 inference_blocked。服务健康正常不表示模型成功预测。无需等待 key，可继续人工标注、导出和本地校验。

```powershell
& .\.venv-public\Scripts\python.exe -m ecommerce_graph_agent prepare-ner --source data/ner/raw/reviewed.json
& .\.venv-public\Scripts\python.exe scripts/services.py stop ml-backend
& .\.venv-public\Scripts\python.exe scripts/services.py stop label-studio
```

校验范围采用 Python Unicode 半开区间 [start,end)，文字必须等于原文切片。Label Studio 的 UTF-16 偏移经转换处理 emoji。拒绝负数、bool 偏移、越界、空区间、非 TAG、重复和重叠。例如独立示例“防漏杯盖”中 [0,3) 与 [2,4) 重叠，整条记录隔离等待人工裁定，不自动选一边。课程 id=677 的原文保留在私有审计。原文件不改写。

预处理按照原文 hash 去重/分组后冻结 train/validation/test；每个拆分与原件有 SHA-256。最终测试集不能参与选 checkpoint。
