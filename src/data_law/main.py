import argparse
from collections.abc import Sequence

from data_law.infra.database.session import create_session_factory
from data_law.ingestion.ingestion import (
    DataJudClient,
    DataJudIngestionService,
    DataJudSettings,
)
from data_law.transformation.silver import sync_bronze_to_silver


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ingestão DataJud do TJSP")
    parser.add_argument(
        "--full",
        action="store_true",
        help="executa a carga histórica dos últimos seis meses",
    )
    arguments = parser.parse_args(argv)

    settings = DataJudSettings()  # type: ignore[call-arg]
    session_factory = create_session_factory()
    service = DataJudIngestionService(
        DataJudClient(settings),
        session_factory,
        silver_sync=lambda: sync_bronze_to_silver(session_factory),
    )
    report = service.run_full() if arguments.full else service.run_incremental()

    print(
        f"Ingestão {report.mode} concluída: {report.pages} página(s), "
        f"{report.candidates} candidato(s), {report.changed} alteração(ões), "
        f"{report.unchanged} processo(s) sem alteração. Silver: "
        f"{report.silver_synced} processo(s), {report.silver_movements} "
        f"movimento(s), {report.silver_warnings} aviso(s)."
    )


if __name__ == "__main__":
    main()
