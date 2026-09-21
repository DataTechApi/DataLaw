from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from data_law.infra.database.base import Base
from data_law.infra.database.model.bronze.bronze_process import (  # noqa: F401
    BronzeDataJudExtract,
)
from data_law.infra.database.model.bronze.ingestion_state import (  # noqa: F401
    BronzeDataJudIngestionState,
)
from data_law.infra.database.settings import DatabaseSettings

# Alembic exposes the configuration object while it runs this module.
config = context.config

# Keep connection details out of alembic.ini and load them from .env instead.
settings = DatabaseSettings()
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importing every model above registers its table in this metadata object.
# Alembic uses it to detect model/schema differences with --autogenerate.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Render SQL without opening a connection to the database."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        include_schemas=True,
        compare_type=True,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations through a short-lived database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
