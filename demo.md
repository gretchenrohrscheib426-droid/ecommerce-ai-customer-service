# 本地演示

首次安装见 [Windows 文档](docs/GETTING_STARTED_WINDOWS.md)。日常在仓库根目录的 PowerShell 执行：

```powershell
& .\.venv-public\Scripts\python.exe -c "import sys; print(sys.executable)"
& .\.venv-public\Scripts\python.exe scripts/run_demo.py start
Invoke-RestMethod http://127.0.0.1:8012/health/ready
```

打开本机聊天地址，先问“随行水杯价格”，展示价格、未上架状态及实际证据；再问“轻旅背包价格”，选择品牌对应的业务 ID；问“随行水杯标签”时指出这是人工合成标注；最后展示“查看订单”被明确拒绝。完整输入与预期在 examples。

不要把截图称为线上部署。README 截图来源于独立合成数据库的真实本地浏览器请求，网络错误与 XSS 等故障用独立 mock 测试说明。

```powershell
& .\.venv-public\Scripts\python.exe scripts/public_verify.py --restart
& .\.venv-public\Scripts\python.exe scripts/run_demo.py stop
```

停止后 API 不可访问；再次 start 不安装、不导入。正式训练、AI 预标注和 DeepSeek 在线调用的未验证状态应在演示中主动说明。
