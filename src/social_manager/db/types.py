from __future__ import annotations

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.types import TypeDecorator


class PortableVector(TypeDecorator[list[float]]):
    """Use pgvector in PostgreSQL and JSON in lightweight local databases."""

    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int | None = None) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dimensions) if self.dimensions else Vector())
        return dialect.type_descriptor(JSON())
