"""Whitelisted reads, bounded timeouts and deterministic connection cleanup."""

import logging
from contextlib import contextmanager

from ..config import Settings
from .validate import BUSINESS_TABLES

logger = logging.getLogger(__name__)


@contextmanager
def connect(root, admin=False):
    import pymysql

    settings = Settings.load(root)
    password = settings.secret("mysql_root" if admin else "mysql")
    if not password:
        raise ValueError("MySQL credentials are not configured")
    try:
        connection = pymysql.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user="root" if admin else settings.mysql_user,
            password=password,
            database=None if admin else settings.mysql_database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=settings.mysql_timeout,
            read_timeout=settings.mysql_timeout,
            write_timeout=settings.mysql_timeout,
            local_infile=False,
            autocommit=False,
        )
        try:
            yield connection
        finally:
            connection.close()
    except pymysql.MySQLError as error:
        logger.error("MySQL operation failed: %s", type(error).__name__)
        raise RuntimeError("MySQL operation unavailable; inspect local service health") from None


def read_business(root):
    tables = {}
    with connect(root) as connection, connection.cursor() as cursor:
        for table in BUSINESS_TABLES:
            cursor.execute(f"SELECT * FROM `{table}` ORDER BY id")
            rows = cursor.fetchall()
            for row in rows:
                for key, value in row.items():
                    if value is not None and not isinstance(value, (str, int, float, bool)):
                        row[key] = str(value)
            tables[table] = rows
    return tables
