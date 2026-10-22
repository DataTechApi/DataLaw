import pytest
from sqlalchemy.orm import sessionmaker

from data_law.infra.database.session import create_session_factory
from data_law.infra.database.settings import DatabaseSettings

DATABASE_URL = "postgresql+psycopg://datalaw:secret@localhost:5432/datalaw_test"


def test_create_session_factory_uses_given_settings() -> None:
    settings = DatabaseSettings(DATABASE_URL=DATABASE_URL)  # type: ignore[call-arg]

    factory = create_session_factory(settings)

    assert isinstance(factory, sessionmaker)
    assert factory.kw["expire_on_commit"] is False
    url = factory.kw["bind"].url
    assert url.drivername == "postgresql+psycopg"
    assert url.host == "localhost"
    assert url.database == "datalaw_test"


def test_create_session_factory_reads_database_url_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)

    factory = create_session_factory()

    assert factory.kw["bind"].url.database == "datalaw_test"
