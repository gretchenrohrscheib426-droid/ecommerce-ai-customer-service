"""Compatibility entry point; index implementation lives with graph schema."""

from ..graph.indexes import BGE_REVISION as BGE_REVISION
from ..graph.indexes import INDEXES as INDEXES
from ..graph.indexes import Embedder as Embedder
from ..graph.indexes import check_index as check_index
from ..graph.indexes import create_indexes as create_indexes

if __name__ == "__main__":
    import runpy

    runpy.run_module("ecommerce_graph_agent.graph.indexes", run_name="__main__")
