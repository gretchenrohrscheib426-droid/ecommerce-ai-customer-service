"""Create only the project's stable business-ID constraints, idempotently."""

from .schema import LABELS


def ensure_constraints(session):
    for label in sorted(LABELS | {"Tag"}):
        session.run(
            f"CREATE CONSTRAINT identity_{label.lower()} IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
        ).consume()
