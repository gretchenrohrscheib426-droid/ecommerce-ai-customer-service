# 独立数据与 MySQL 同步

`scripts/generate_demo_data.py` 从独立生成器产生 12 表 business.json、products.json、ner_sample.json；来源明确为 Synthetic Demo Data。3 个 SPU、3 个 SKU、2 个品牌含一个同名消歧案例，不包含课程商品或个人字段。

终端位于仓库根目录，先完成 Windows 安装，再运行下面命令。MySQL 8.4 二进制单独下载；创建本仓库专属数据目录，不注册 Windows 服务。默认只监听 127.0.0.1:3308。

```powershell
& .\.venv-public\Scripts\python.exe -c "import sys; print(sys.executable)"
& .\.venv-public\Scripts\python.exe scripts/generate_demo_data.py --check
& .\.venv-public\Scripts\python.exe scripts/download_runtimes.py --mysql-only
& .\.venv-public\Scripts\python.exe scripts/configure_demo_mysql.py configure --port 3308
& .\.venv-public\Scripts\python.exe scripts/services.py start mysql
& .\.venv-public\Scripts\python.exe scripts/configure_demo_mysql.py secure
& .\.venv-public\Scripts\python.exe scripts/init_demo_mysql.py
& .\.venv-public\Scripts\python.exe scripts/serving_mode.py build
& .\.venv-public\Scripts\python.exe scripts/sync_graph.py structured --source mysql
& .\.venv-public\Scripts\python.exe scripts/sync_graph.py tags
& .\.venv-public\Scripts\python.exe scripts/create_indexes.py
$env:ECOMMERCE_PUBLIC_INTEGRATION='1'
$env:ECOMMERCE_GRAPH_WRITABLE='1'
& .\.venv-public\Scripts\python.exe -m pytest tests/integration/test_mysql_connection.py tests/integration/test_graph_sync.py tests/integration/test_neo4j_connection.py tests/integration/test_hybrid_retrieval.py tests/integration/test_chat_pipeline.py -q
Remove-Item Env:ECOMMERCE_GRAPH_WRITABLE
& .\.venv-public\Scripts\python.exe scripts/serving_mode.py serve
& .\.venv-public\Scripts\python.exe scripts/services.py start api
& .\.venv-public\Scripts\python.exe scripts/services.py stop mysql
```

首次创建数据目录之后应立即 start、secure；生成的随机密码只保存在忽略的 credentials.json。端口冲突请在首次 configure 时换成空闲端口，例如 3310。已有数据目录、异构/部分 schema、未知账号密码会拒绝覆盖，必须先人工检查。停止 MySQL 使用 SQL SHUTDOWN；不能通过杀掉任意 mysqld.exe 处理端口冲突。

成功信号：init_demo_mysql 输出 PASS 并列出 12 表计数；sync_graph 输出对账文件路径；重复导入 nodes_created 和 relationships_created 为 0。只读账号只能 SELECT，root 仅用于新示例初始化与停止服务。

数据先由 graph_plan 校验 ID、端点和重复，再在 Neo4j 事务里核对两端；重复数据有统计，缺失端点报错，不伪造节点。对账保存在 artifacts/reconciliation/graph_sync_report.json。公开 Tag 为人工编写，model_sha256 使用明确的 manual-fixture 标识。

课程材料中 id=677 的重叠跨度、36 行缺属性端点和 14 行缺属性值端点属于私有审计，不在公开仓库分发原文。处理策略是保留原件、输出隔离记录及规则、待人工裁定；公开回归测试用独立构造的非法输入验证拒绝路径。课程 1529/1641 静态预期不能替代任何实际导入报告。

Docker 配置是可选路线，独立于本机已执行的原生 Windows 路线；未运行容器时状态保持 NOT_RUN。
