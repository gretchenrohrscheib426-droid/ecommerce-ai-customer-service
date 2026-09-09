"""Compatibility exports for the original reproduction entry points."""

from ..graph.schema import GROUPS as GROUPS
from ..graph.schema import LABELS as LABELS
from .reconciliation import ensure_namespace as ensure_namespace
from .reconciliation import snapshot as snapshot
from .table_sync import sync_course as sync_course
from .table_sync import sync_plan as sync_plan
from .text_sync import sync_tags as sync_tags
