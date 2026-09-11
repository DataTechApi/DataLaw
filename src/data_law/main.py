from data_law.ingestion.ingestion import DataJudClient, DataJudSettings
from data_law.ingestion.storage import save_raw_response


def main() -> None:
    settings = DataJudSettings()
    client = DataJudClient(settings)

    tribunal = "api_publica_tjsp"

    body = {
        "size": 100,
        "track_total_hits": False,
        "query": {
            "bool": {
                "filter": [
                    {"terms": {"movimentos.codigo": [22, 246]}},
                    {
                        "range": {
                            "movimentos.dataHora": {
                                "gte": "now-6M",
                                "lte": "now",
                            }
                        }
                    },
                ]
            }
        },
    }

    payload = client.ingest(tribunal, body)
    file_path = save_raw_response("tjsp", payload)

    print(f"Deu certo aqui {file_path}")


if __name__ == "__main__":
    main()
