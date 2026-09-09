# 来源与第三方边界

课程来源：《尚硅谷大模型技术之电商图谱 V1.1.0》及其配套资料。课程 DOCX、内嵌 Neo4j/Label Studio 教程、架构图、SQL、NER 数据、安装器和原前端保持私有；没有确认其再分发许可。公开实现、样例、页面和测试为本次任务重新编写，不将课程资料整体加 MIT。

以下仅通过官方安装/下载脚本取得，未捆绑分发；具体条款以对应固定版本随包 LICENSE/NOTICE 为准。

|组件|固定版本/来源|许可说明|
|---|---|---|
|Neo4j Community|5.26.30，dist.neo4j.org|GPL-3.0 社区版；运行包内 LICENSE/第三方 notices 保留|
|Eclipse Temurin JDK|21.0.12.1+1，Adoptium 官方 GitHub|GPL-2.0 with Classpath Exception，附其他第三方声明|
|MySQL Community|8.4.11，cdn.mysql.com；仅本地运行；公开合成schema亦可使用|GPLv2 社区发行及随包第三方条款|
|Label Studio|1.23.0，HumanSignal；仅私有服务|Apache-2.0，依赖各自条款|
|Label Studio ML Backend|HumanSignal revision 54206e6dcb7f1ca4ebf706f2399eca52612f4d8e|Apache-2.0，上游通知保留|
|BERT base Chinese|google-bert 固定 revision，见 MODEL_CARD|模型卡 Apache-2.0；私有微调数据/权重不分发|
|BGE small zh v1.5|BAAI 固定 revision，见 MODEL_CARD|模型卡 MIT；下载脚本保留模型说明|
|PyTorch、Transformers、sentence-transformers、Neo4j Python Driver、FastAPI 等|envs 实测锁和本地包元数据|各自许可证，项目 MIT 不覆盖这些软件|

`scripts/java/LocalNeo4j.java` 是调用 Neo4j 启停 API 的本地适配源码，没有捆绑编译后的类或 Neo4j 二进制；若未来分发链接产物或修改第三方软件，应针对 GPL 等条款重新审查，不能据本项目许可直接再分发。

CI Actions 来自 actions 官方仓库；固定 SHA 于 2026-09-09 通过 GitHub git/ref API 核实。公开端无 Marked/DOMPurify CDN 或课程 vendor 文件。下载来源、大小、摘要在实际运行目录生成，缓存不进 Git。
