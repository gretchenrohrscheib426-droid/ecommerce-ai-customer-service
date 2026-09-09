# 仓库协作规则

本目录是独立公开示例的本地 Git 工作区。课程原始资料和私有复现位于父工作区，不得递归复制进来。

- 可在用户明确授权的目标和范围内修改、测试、提交与推送。发布前必须验证发布清单、来源、秘密、测试与依赖审计；禁止强制推送。
- 保留未提交改动。所有 Python 命令使用明确的解释器；打印 sys.executable。不要更新父目录三个课程 Conda 环境。
- 公开示例仅用 data/sample，标注 Tag 是人工合成 fixture。不能冒充训练推理、真实企业商品或线上模型。
- 配置从环境变量、.env、本地 runtime.json 读取；只检查密钥是否存在，日志不得记录明文问题或密码。
- 数据库同步必须限定 independent-sample 专属实例，业务主键决定节点身份；校验失败应中止并记录，不能伪造端点。
- Cypher 只接受服务端模板和验证后的参数。禁止增加客户端 raw Cypher、任意 APOC、文件导入或写查询。
- 同名/低置信候选必须澄清；无结果不能编造答案；缺少模型返回明确阻塞状态。
- 修改需对应真实回归证据。通过、失败、未运行分别记录，mock、实际数据库、浏览器和在线模型分开。
- 发布前执行 scripts/check_public_boundary.py 和 scripts/validate_release.py --run；已知漏洞、未核实许可不得写 READY。
- 本次明确授权的发布目标为 gretchenrohrscheib426-droid/ecommerce-ai-customer-service 的 main；先保留远程 archive 备份分支，再在工作分支验证后普通合并。未来发布仍须遵守当次用户授权范围。
