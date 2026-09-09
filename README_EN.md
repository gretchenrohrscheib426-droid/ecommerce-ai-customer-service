# E-commerce Knowledge Graph AI Customer Service

A local portfolio project developed from an e-commerce knowledge-graph course. All public business and annotation fixtures are independently authored **Synthetic Demo Data**.

The request pipeline resolves intent and entity identity, optionally retrieves BGE/full-text candidates, asks for clarification when needed, executes one of nine fixed Cypher templates, and renders database evidence. Exact names and approved unique aliases bypass fuzzy retrieval. DeepSeek is optional and may only select existing evidence; online inference has not been verified for this release.

The repository includes a Label Studio configuration and independent ML Backend, BERT TAG preprocessing/training/prediction/evaluation, MySQL-to-Neo4j synchronization, provenance-aware Tags, hybrid retrieval, bounded orchestration, FastAPI, a static chat UI and regression/integration tests.

Start with [Windows setup](docs/GETTING_STARTED_WINDOWS.md). The [Chinese README](README.md) contains the architecture, commands, questions and screenshot. [release_validation.json](release_validation.json) records individual check states; GitHub workflow status must be read from the actual run.

Public fixtures contain three SPUs, including two different products with the same name. Their Tags are manually authored examples, not BERT predictions. No trained checkpoint, full-training metric, retrieval benchmark, production deployment or real customer outcome is claimed. A tiny random-model contract test verifies training APIs only.

See [SOURCE_MAP](SOURCE_MAP.md) for course lineage versus individual engineering changes, [NOTICE](NOTICE.md) for attribution and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md) for separate upstream licenses. MIT applies to redistributable repository code and original synthetic fixtures. Private course archives, annotations, SQL, model weights and credentials are excluded.
