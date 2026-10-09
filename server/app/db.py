import logging
from collections.abc import Iterator
from enum import Enum
from functools import lru_cache

from sqlalchemy import Engine, inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (registers tables)
from app.config import get_settings

log = logging.getLogger(__name__)


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return create_engine(settings.db_url, connect_args={"check_same_thread": False})


def _sql_literal(value: object) -> str | None:
    if isinstance(value, Enum):
        value = value.name  # SQLAlchemy stores enum members by name
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return None


def add_missing_columns(engine: Engine) -> None:
    """Add columns that exist in the models but not in an older database file.

    Stand-in for migrations while the schema only grows: new columns get their
    scalar default (or NULL), so existing projects keep working.
    """
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in SQLModel.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                column_type = column.type.compile(dialect=engine.dialect)
                default = (
                    column.default.arg if column.default is not None and column.default.is_scalar else None
                )
                literal = _sql_literal(default)
                clause = f" DEFAULT {literal}" if literal is not None else ""
                conn.execute(
                    text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}{clause}')
                )
                log.info("Added column %s.%s", table.name, column.name)


def init_db(reset: bool = False) -> None:
    engine = get_engine()
    if reset:
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    add_missing_columns(engine)


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
