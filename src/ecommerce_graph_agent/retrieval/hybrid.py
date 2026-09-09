"""Vector/fulltext RRF retrieval, with canonical typed candidates."""

from .schemas import CandidateEntity
from .search import Retriever


class HybridRetriever(Retriever):
    def candidates(self, text, label=None, top_k=5) -> list[CandidateEntity]:
        result = []
        for row in self.hybrid(text, label, top_k):
            metadata = row["metadata"]
            channels = row["channels"]
            result.append(
                CandidateEntity(
                    label=metadata["label"],
                    canonical_id=metadata["canonical_id"],
                    canonical_name=metadata["canonical_name"],
                    score=row["score"],
                    source="hybrid" if len(channels) > 1 else next(iter(channels)),
                    raw_metadata={**metadata, "channels": channels, "score_type": "RRF rank fusion"},
                )
            )
        return result
