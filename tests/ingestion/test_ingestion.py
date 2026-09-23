from unittest.mock import MagicMock, patch

import requests

from data_law.ingestion.ingestion import DataJudClient, DataJudSettings


def make_client() -> DataJudClient:
    settings = DataJudSettings(
        DATAJUD_API_KEY="fake-key", url="https://fake.datajud.test"
    )
    return DataJudClient(settings)


@patch("data_law.ingestion.ingestion.requests.post")
def test_ingest_returns_json_and_calls_correct_url(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"hits": {"hits": []}}
    mock_post.return_value = mock_response

    client = make_client()
    result = client.ingest("api_publica_tjsp", {"query": "something"})

    assert result == {"hits": {"hits": []}}
    mock_response.raise_for_status.assert_called_once()
    mock_post.assert_called_once_with(
        "https://fake.datajud.test/api_publica_tjsp/_search",
        json={"query": "something"},
        headers={"Authorization": "APIKey fake-key"},
        timeout=90,
    )


@patch("data_law.ingestion.ingestion.requests.post")
def test_ingest_retries_after_failure_and_then_succeeds(mock_post):
    mock_response_ok = MagicMock()
    mock_response_ok.json.return_value = {"ok": True}

    mock_post.side_effect = [
        requests.exceptions.ConnectionError("simulated network failure"),
        mock_response_ok,
    ]

    client = make_client()
    client.ingest.retry.wait = lambda *args, **kwargs: 0

    result = client.ingest("api_publica_tjsp", {})

    assert result == {"ok": True}
    assert mock_post.call_count == 2
