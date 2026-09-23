from typing import ClassVar

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    pass


class SchemaBase(Base):
    __abstract__ = True

    schema_name: ClassVar[str]

    @declared_attr.directive
    def __table_args__(cls) -> dict[str, str] | tuple[object, ...]:
        return {"schema": cls.schema_name}


class BronzeBase(SchemaBase):
    __abstract__ = True
    schema_name = "bronze"


class SilverBase(SchemaBase):
    __abstract__ = True
    schema_name = "silver"


class GoldBase(SchemaBase):
    __abstract__ = True
    schema_name = "gold"
