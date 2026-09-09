"""Compatibility exports for existing command-line integrations."""

from ..graph.queries import TEMPLATES as TEMPLATES
from ..graph.queries import compile_plan as compile_plan
from ..graph.queries import execute as execute
from ..security.cypher_guard import validate_query as validate_query
