"""Create the application workflow from initialized, local dependencies."""

import json

from ..agent.orchestrator import ChatService
from ..retrieval.hybrid import HybridRetriever


def build_service(settings, instance, embedder, dataset):
    aliases_path = settings.root / "configs/approved-aliases.json"
    aliases = json.loads(aliases_path.read_text(encoding="utf-8")) if aliases_path.exists() else {}
    retriever = HybridRetriever(
        instance, embedder, aliases=aliases, min_cosine=settings.entity_alignment_threshold
    )
    return ChatService(settings.root, retriever, instance, online=settings.online_enabled, dataset=dataset)
