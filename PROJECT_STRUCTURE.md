# 公开仓库目录与职责

仅展示可公开的源文件，不列被忽略的模型、数据库、凭据、原件和日志。当前包为 src/ecommerce_graph_agent，db/、qa/ 等兼容导出保留。此目录是父级课程私有项目的独立公开工作区，不是另一个替代课程系统。

- src：数据模型、同步、图结构、检索、受控问答和 API。
- annotation：独立 ML Backend 与 SDK 适配。
- scripts：明确安装、构建、运行、对账、验证和停止入口。
- tests：离线单元、显式真实数据库集成、API 与浏览器端到端。
- docs：操作指南、来源、评测和求职证据；.github 是尚未执行的 CI 配置。
- envs：三环境声明和本机实测锁。data/sample 与 examples 都是独立合成例。

完整候选文件树：

```text
├── .editorconfig
├── .env.example
├── .gitattributes
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── config.yml
│   │   └── feature_request.yml
│   ├── dependabot.yml
│   ├── pull_request_template.md
│   └── workflows/
│       ├── ci.yml
│       ├── release-check.yml
│       ├── security.yml
│       └── tests.yml
├── .gitignore
├── .pre-commit-config.yaml
├── AGENTS.md
├── ARCHITECTURE.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── NOTICE.md
├── PROJECT_STRUCTURE.md
├── PUBLISH_REVIEW.md
├── README.md
├── README_EN.md
├── ROADMAP.md
├── SECURITY.md
├── SOURCE_MAP.md
├── THIRD_PARTY_NOTICES.md
├── annotation/
│   └── ml_backend/
│       ├── _wsgi.py
│       └── model.py
├── cache.db
├── configs/
│   ├── label_studio.xml
│   └── profiles/
│       ├── course-reference.json
│       └── safe-demo.json
├── data/
│   ├── README.md
│   └── sample/
│       ├── README.md
│       ├── annotation_tasks.json
│       ├── business.json
│       ├── ner_sample.json
│       └── products.json
├── demo.md
├── docker-compose.yml
├── docs/
│   ├── AGENT_WORKFLOW.md
│   ├── API.md
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── BEGINNER_GUIDE.md
│   ├── CYPHER_SECURITY.md
│   ├── DATA_CARD.md
│   ├── DATA_PIPELINE.md
│   ├── DECISIONS.md
│   ├── DEMO_GUIDE.md
│   ├── ENVIRONMENT_SETUP.md
│   ├── EVALUATION.md
│   ├── GETTING_STARTED_WINDOWS.md
│   ├── HYBRID_RETRIEVAL.md
│   ├── INTERVIEW_GUIDE.md
│   ├── KNOWLEDGE_GRAPH.md
│   ├── LIMITATIONS.md
│   ├── MODEL_CARD.md
│   ├── NER_PIPELINE.md
│   ├── PUBLIC_PRIVATE_BOUNDARY.md
│   ├── RESUME_EVIDENCE.md
│   ├── RESUME_PROOF.md
│   ├── RUN_PUBLIC_WINDOWS.md
│   ├── RUN_WINDOWS.md
│   ├── SOURCE_MAP.md
│   ├── TRAINING_GUIDE.md
│   ├── TROUBLESHOOTING.md
│   ├── VALIDATION.md
│   ├── assets/
│   │   ├── .gitkeep
│   │   └── public-demo.png
│   └── dependency_licenses.json
├── environment.yml
├── envs/
│   ├── ci-requirements.txt
│   ├── graph.yml
│   ├── label-studio.yml
│   ├── locks/
│   │   └── public/
│   │       ├── README.md
│   │       ├── development-pip-win64.txt
│   │       └── public-pip-win64.txt
│   ├── ml-backend.yml
│   └── public-requirements.in
├── examples/
│   ├── README.md
│   ├── expected_responses.json
│   └── sample_questions.json
├── materials_private/
│   └── .gitkeep
├── models/
│   ├── .gitkeep
│   └── README.md
├── publish_manifest.json
├── pyproject.toml
├── release_validation.json
├── requirements-dev.txt
├── requirements.txt
├── scripts/
│   ├── bootstrap_windows.ps1
│   ├── check_environment.py
│   ├── check_public_boundary.py
│   ├── check_services.ps1
│   ├── configure_annotation.py
│   ├── create_indexes.py
│   ├── download_models.py
│   ├── download_runtimes.py
│   ├── generate_demo_data.py
│   ├── generate_sample.py
│   ├── init_demo_mysql.py
│   ├── java/
│   │   └── LocalNeo4j.java
│   ├── public_bootstrap.ps1
│   ├── public_verify.py
│   ├── run_demo.py
│   ├── run_tests.ps1
│   ├── sample_demo.py
│   ├── services.py
│   ├── serving_mode.py
│   ├── source_check.py
│   ├── start_api.ps1
│   ├── sync_graph.py
│   ├── validate_release.py
│   └── verify_manifest.py
├── src/
│   └── ecommerce_graph_agent/
│       ├── __init__.py
│       ├── __main__.py
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── intent.py
│       │   ├── orchestrator.py
│       │   └── state.py
│       ├── cli.py
│       ├── config.py
│       ├── datasync/
│       │   ├── __init__.py
│       │   ├── mysql_reader.py
│       │   ├── neo4j_writer.py
│       │   ├── reconciliation.py
│       │   ├── sync.py
│       │   ├── table_sync.py
│       │   ├── text_sync.py
│       │   └── validate.py
│       ├── db/
│       │   ├── __init__.py
│       │   ├── mysql.py
│       │   └── neo4j.py
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── constraints.py
│       │   ├── indexes.py
│       │   ├── queries.py
│       │   └── schema.py
│       ├── health.py
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── deepseek_client.py
│       │   └── prompts.py
│       ├── logging_config.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── ner/
│       │       ├── __init__.py
│       │       ├── data_validation.py
│       │       ├── eval.py
│       │       ├── evaluate.py
│       │       ├── predict.py
│       │       ├── process.py
│       │       ├── schemas.py
│       │       └── train.py
│       ├── qa/
│       │   ├── __init__.py
│       │   ├── cypher.py
│       │   ├── provider.py
│       │   ├── schema.py
│       │   └── service.py
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── entity_alignment.py
│       │   ├── hybrid.py
│       │   ├── indexes.py
│       │   ├── schemas.py
│       │   └── search.py
│       ├── security/
│       │   ├── __init__.py
│       │   └── cypher_guard.py
│       └── web/
│           ├── __init__.py
│           ├── app.py
│           ├── schemas.py
│           ├── service.py
│           └── static/
│               ├── app.js
│               ├── index.html
│               └── styles.css
└── tests/
    ├── conftest.py
    ├── e2e/
    │   ├── chat_browser.mjs
    │   └── test_api.py
    ├── integration/
    │   ├── test_chat_pipeline.py
    │   ├── test_graph_sync.py
    │   ├── test_hybrid_retrieval.py
    │   ├── test_mysql_connection.py
    │   ├── test_neo4j_connection.py
    │   └── test_public_ci.py
    └── unit/
        ├── test_annotation.py
        ├── test_annotation_http.py
        ├── test_api_schemas.py
        ├── test_bootstrap.py
        ├── test_config.py
        ├── test_cypher_guard.py
        ├── test_data.py
        ├── test_entity_alignment.py
        ├── test_indexes.py
        ├── test_neo4j_writer.py
        ├── test_ner.py
        ├── test_ner_alignment.py
        ├── test_ner_validation.py
        ├── test_public_boundary.py
        ├── test_qa.py
        ├── test_split.py
        ├── test_web.py
        └── test_workflow.py
```

变动数量以父级私有最终交付报告为准；重命名按旧路径移除和新路径新增统计，不等于代码被删除。
