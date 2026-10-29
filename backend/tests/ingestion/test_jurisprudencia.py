import json
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from data_law.infra.database.model.silver.jurisprudencia import (
    SilverDataJudJurisprudencia,
)
from data_law.ingestion import jurisprudencia
from data_law.ingestion.jurisprudencia import (
    BNPApiClient,
    _sanitize_term,
    calculate_source_hash,
    clean_html,
    fetch_and_save_precedents_for_subject,
    sync_all_active_subjects,
)


class FakeBNPClient:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    def buscar(self, termo: str, max_resultados: int = 5) -> list[dict[str, Any]]:
        self.calls.append((termo, max_resultados))
        return self.results


class FakeSession:
    def __init__(self, existing_hashes: set[str] | None = None) -> None:
        self.existing_hashes = existing_hashes or set()
        self.added: list[SilverDataJudJurisprudencia] = []
        self.rows: list[SimpleNamespace] = []
        self.executed_params: dict[str, Any] | None = None

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    @contextmanager
    def begin(self):
        yield self

    def scalar(self, statement: Any) -> object | None:
        source_hash = statement.whereclause.right.value
        return object() if source_hash in self.existing_hashes else None

    def add(self, item: SilverDataJudJurisprudencia) -> None:
        self.added.append(item)

    def execute(self, statement: object, params: dict[str, Any]) -> MagicMock:
        self.executed_params = params
        result = MagicMock()
        result.fetchall.return_value = self.rows
        return result


def _factory(session: FakeSession):
    return lambda: session


def _bnp_response(status_code: int, body: dict[str, Any]) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.content = json.dumps(body).encode("utf-8")
    return response


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, ""),
        ("", ""),
        ("<p>Tese&nbsp;<b>firmada</b></p>", "Tese firmada"),
        ("&lt;b&gt;texto&lt;/b&gt;   com\n\nespaços", "texto com espaços"),
    ],
)
def test_clean_html_removes_tags_entities_and_extra_whitespace(
    raw: str | None, expected: str
) -> None:
    assert clean_html(raw) == expected


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        ("DIREITO DO CONSUMIDOR", "CONSUMIDOR"),
        ("Direito Civil", "Civil"),
        ("DIREITO", "DIREITO"),
        ("Indenização por Dano Moral", "Indenização por Dano Moral"),
        (
            "Responsabilidade (Civil)/Objetiva do Estado",
            "Responsabilidade Civil Objetiva Estado",
        ),
        (
            "Rescisão do Contrato de Trabalho por Justa Causa",
            "Rescisão Contrato Trabalho por",
        ),
        ("a / b", ""),
    ],
)
def test_sanitize_term_drops_short_tokens_generic_prefix_and_limits_size(
    term: str, expected: str
) -> None:
    assert _sanitize_term(term) == expected


def test_source_hash_uses_only_key_fields_and_is_order_independent() -> None:
    data = {
        "tribunal_sigla": "STJ",
        "identificador_precedente": "RR 1234",
        "assunto_codigo": 7779,
        "titulo": "Título",
    }
    reordered = dict(reversed(list(data.items())))

    assert calculate_source_hash(data) == calculate_source_hash(reordered)
    assert calculate_source_hash(data) == calculate_source_hash(
        {**data, "ementa": "ignorada"}
    )
    assert calculate_source_hash(data) != calculate_source_hash(
        {**data, "assunto_codigo": 1}
    )
    assert len(calculate_source_hash(data)) == 64


@patch("data_law.ingestion.jurisprudencia.requests.post")
def test_buscar_sends_filter_payload_and_returns_results(mock_post) -> None:
    results = [{"tipo": "RR", "nr": "1234"}]
    mock_post.return_value = _bnp_response(200, {"resultados": results})

    client = BNPApiClient(base_url="https://fake.bnp.test", timeout=5)
    found = client.buscar("  dano moral  ", max_resultados=50)

    assert found == results
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args == ("https://fake.bnp.test",)
    assert kwargs["timeout"] == 5
    filtro = kwargs["json"]["filtro"]
    assert filtro["buscaGeral"] == "dano moral"
    assert filtro["tamanhoPagina"] == 20
    assert filtro["orgaos"] == ["STJ", "STF", "TJSP"]
    assert filtro["tipos"] == ["RR", "RG", "SUM", "IRDR", "IAC"]


@patch("data_law.ingestion.jurisprudencia.requests.post")
def test_buscar_uses_given_courts_and_types(mock_post) -> None:
    mock_post.return_value = _bnp_response(200, {"resultados": []})

    BNPApiClient().buscar("dano", orgaos=["STF"], tipos=["SUM"], max_resultados=3)

    filtro = mock_post.call_args.kwargs["json"]["filtro"]
    assert filtro["orgaos"] == ["STF"]
    assert filtro["tipos"] == ["SUM"]
    assert filtro["tamanhoPagina"] == 3


@pytest.mark.parametrize("term", ["", "   "])
@patch("data_law.ingestion.jurisprudencia.requests.post")
def test_buscar_skips_request_for_blank_term(mock_post, term: str) -> None:
    assert BNPApiClient().buscar(term) == []
    mock_post.assert_not_called()


@patch("data_law.ingestion.jurisprudencia.requests.post")
def test_buscar_returns_empty_list_for_non_200_status(mock_post) -> None:
    mock_post.return_value = _bnp_response(503, {"resultados": [{"nr": "1"}]})

    assert BNPApiClient().buscar("dano moral") == []


@patch("data_law.ingestion.jurisprudencia.requests.post")
def test_buscar_returns_empty_list_when_body_has_no_results(mock_post) -> None:
    mock_post.return_value = _bnp_response(200, {"total": 0})

    assert BNPApiClient().buscar("dano moral") == []


@patch("data_law.ingestion.jurisprudencia.requests.post")
def test_buscar_returns_empty_list_on_network_error(mock_post) -> None:
    mock_post.side_effect = requests.exceptions.ConnectionError("sem rede")

    client = BNPApiClient()
    client.buscar.retry.wait = lambda *args, **kwargs: 0

    assert client.buscar("dano moral") == []


def test_fetch_skips_search_when_sanitized_term_is_empty() -> None:
    client = FakeBNPClient([{"tipo": "RR", "nr": "1", "tese": "x"}])
    session = FakeSession()

    inserted = fetch_and_save_precedents_for_subject(
        _factory(session), assunto_codigo=1, assunto_nome="a / b", client=client
    )

    assert inserted == 0
    assert client.calls == []
    assert session.added == []


def test_fetch_returns_zero_without_opening_session_when_no_results() -> None:
    client = FakeBNPClient([])
    session_factory = MagicMock()

    inserted = fetch_and_save_precedents_for_subject(
        session_factory, assunto_codigo=1, assunto_nome="Dano Moral", client=client
    )

    assert inserted == 0
    assert client.calls == [("Dano Moral", 3)]
    session_factory.assert_not_called()


def test_fetch_persists_precedent_with_cleaned_text() -> None:
    client = FakeBNPClient(
        [
            {
                "tipo": "RR",
                "nr": "1234",
                "orgao": "STJ",
                "questao": "<p>Cabe dano moral?</p>",
                "tese": "<p>Sim, cabe&nbsp;dano moral.</p>",
            }
        ]
    )
    session = FakeSession()

    inserted = fetch_and_save_precedents_for_subject(
        _factory(session),
        assunto_codigo=10433,
        assunto_nome="DIREITO DO CONSUMIDOR",
        client=client,
        max_precedentes=2,
    )

    assert inserted == 1
    assert client.calls == [("CONSUMIDOR", 2)]
    [saved] = session.added
    assert saved.tribunal_sigla == "STJ"
    assert saved.identificador_precedente == "RR 1234"
    assert saved.titulo == "Cabe dano moral?"
    assert saved.ementa == "Cabe dano moral?"
    assert saved.tese == "Sim, cabe dano moral."
    assert saved.assunto_codigo == 10433
    assert saved.assunto_nome == "DIREITO DO CONSUMIDOR"
    assert saved.numero_processo is None
    assert saved.source_hash == calculate_source_hash(
        {
            "tribunal_sigla": "STJ",
            "identificador_precedente": "RR 1234",
            "assunto_codigo": 10433,
            "titulo": "Cabe dano moral?",
        }
    )


def test_fetch_uses_fallbacks_for_missing_fields() -> None:
    client = FakeBNPClient(
        [
            {"id": "abc-1", "tese": "Tese sem questão"},
            {"tese": "Outra tese"},
        ]
    )
    session = FakeSession()

    inserted = fetch_and_save_precedents_for_subject(
        _factory(session), assunto_codigo=1, assunto_nome="Dano Moral", client=client
    )

    assert inserted == 2
    first, second = session.added
    assert first.identificador_precedente == "abc-1"
    assert first.tribunal_sigla == "CNJ"
    assert first.titulo == "abc-1 - Dano Moral"
    assert first.ementa == "Tese sem questão"
    assert second.identificador_precedente == "Precedente"
    assert second.titulo == "Precedente - Dano Moral"


def test_fetch_truncates_title_to_250_characters() -> None:
    questao = "q" * 300
    client = FakeBNPClient([{"tipo": "RG", "nr": "9", "questao": questao}])
    session = FakeSession()

    fetch_and_save_precedents_for_subject(
        _factory(session), assunto_codigo=1, assunto_nome="Dano Moral", client=client
    )

    [saved] = session.added
    assert saved.titulo == "q" * 250
    assert saved.ementa == questao
    assert saved.tese == ""


def test_fetch_skips_precedent_without_thesis_or_question() -> None:
    client = FakeBNPClient([{"tipo": "RR", "nr": "1", "tese": "<p> </p>"}])
    session = FakeSession()

    inserted = fetch_and_save_precedents_for_subject(
        _factory(session), assunto_codigo=1, assunto_nome="Dano Moral", client=client
    )

    assert inserted == 0
    assert session.added == []


def test_fetch_skips_precedent_already_saved() -> None:
    known = {"tipo": "RR", "nr": "1", "orgao": "STJ", "questao": "Já salvo"}
    new = {"tipo": "RR", "nr": "2", "orgao": "STJ", "questao": "Novo"}
    known_hash = calculate_source_hash(
        {
            "tribunal_sigla": "STJ",
            "identificador_precedente": "RR 1",
            "assunto_codigo": 1,
            "titulo": "Já salvo",
        }
    )
    session = FakeSession(existing_hashes={known_hash})

    inserted = fetch_and_save_precedents_for_subject(
        _factory(session),
        assunto_codigo=1,
        assunto_nome="Dano Moral",
        client=FakeBNPClient([known, new]),
    )

    assert inserted == 1
    assert [item.identificador_precedente for item in session.added] == ["RR 2"]


def test_sync_all_active_subjects_fetches_each_frequent_subject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    session.rows = [
        SimpleNamespace(codigo="10433", nome="Dano Moral", qtd=120),
        SimpleNamespace(codigo=7779, nome="Indenização", qtd=45),
    ]
    calls: list[tuple[int, str]] = []

    def fake_fetch(**kwargs: Any) -> int:
        calls.append((kwargs["assunto_codigo"], kwargs["assunto_nome"]))
        return 2

    monkeypatch.setattr(jurisprudencia, "BNPApiClient", lambda: object())
    monkeypatch.setattr(
        jurisprudencia, "fetch_and_save_precedents_for_subject", fake_fetch
    )

    report = sync_all_active_subjects(_factory(session), min_processos=40)

    assert session.executed_params == {"min_proc": 40}
    assert calls == [(10433, "Dano Moral"), (7779, "Indenização")]
    assert report.total == 2
    assert report.inserted == 4


def test_sync_all_active_subjects_with_no_subjects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(jurisprudencia, "BNPApiClient", lambda: object())

    report = sync_all_active_subjects(_factory(FakeSession()))

    assert report.total == 0
    assert report.inserted == 0
