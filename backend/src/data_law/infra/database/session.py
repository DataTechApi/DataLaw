from collections.abc import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from data_law.infra.database.settings import DatabaseSettings

SessionFactory = Callable[[], Session]


def create_session_factory(
    settings: DatabaseSettings | None = None,
) -> sessionmaker[Session]:
    """Create short-lived SQLAlchemy sessions for the configured PostgreSQL database."""
    database_settings = settings or DatabaseSettings()  # type: ignore[call-arg]
    engine = create_engine(database_settings.database_url)
    return sessionmaker(bind=engine, expire_on_commit=False)
