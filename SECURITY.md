# 安全说明

发布前在隔离 Python 3.12 CPU 环境实际升级并验证 Transformers 5.16.1、PyTorch 2.14.0、Accelerate 1.15.0、Datasets 5.0.1。旧版已知漏洞未用忽略规则绕过；变更涉及训练参数与日志接口，使用随机微型 BERT 运行真实训练入口、保存 safetensors、分词器重载回归，并重新执行真实 BGE 索引/检索。

扫描完整第三方包集合（包含传递依赖），CPU torch 构建按上游版本审计，避免因 +cpu 不在 PyPI 而漏扫。首次环境审计发现的漏洞报告保存在本地；最终结果和范围见 release_validation.json、envs/locks/public/security-requirements.txt。软件包自己的源码由边界检查、代码审阅与测试覆盖；漏洞数据库没有记录不代表绝对安全。

依赖来源：[Transformers](https://pypi.org/project/transformers/5.16.1/)、[PyTorch](https://pypi.org/project/torch/2.14.0/)、[Accelerate](https://pypi.org/project/accelerate/1.15.0/)、[Datasets](https://pypi.org/project/datasets/5.0.1/)。固定下载只使用受控模型名和 revision、safetensors、本地文件、禁用远程模型代码；不得载入陌生 pickle 或私自更换 checkpoint。

HTTP 不接收原始 Cypher；查询为固定模板，ID/limit 校验、最多 20 行、5 秒数据库超时，业务数据库 serve 模式只读。实际尝试写入必须被拒绝；system 库不在该只读范围内。数据库与 API 仅绑定本机；示例无生产账号/租户隔离，不能直接公网暴露。

日志不写完整问题、模型原文、凭据或授权头；密钥仅后端本地配置。发布扫描候选、暂存区与可达历史，输出路径/规则而非匹配内容。发现疑似泄露请通过仓库的私密安全报告渠道联系维护者；未启用该渠道时不要在公开 issue 粘贴秘密。

Label Studio 与独立 ML Backend 是单独安装与验收范围，不继承图环境的扫描结论。DeepSeek 在线调用和正式 BERT 训练未验证；本地演示不处理真实订单或客户数据。
