"""Real-time and batch ingestion of jurisprudence and precedents from CNJ BNP.

Directly integrates with the public Pangea/BNP API.
Adheres strictly to LGPD data minimization guidelines: stores only public procedural
precedents, ementas, binding legal theses, and court identifications.
"""

import hashlib
import html
import json
import logging
import re
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import requests
from sqlalchemy import select, text
from tenacity import retry, stop_after_attempt, wait_exponential

from data_law.infra.database.model.silver.jurisprudencia import (
    SilverDataJudJurisprudencia,
)
from data_law.infra.database.session import SessionFactory, create_session_factory

logger = logging.getLogger(__name__)

BNP_API_URL = "https://pangeabnp.pdpj.jus.br/api/v1/precedentes"


def clean_html(text_val: str | None) -> str:
    """Remove HTML tags and entities."""
    if not text_val:
        return ""
    unescaped = html.unescape(text_val)
    cleaned = re.sub(r"<[^>]+>", " ", unescaped)
    return re.sub(r"\s+", " ", cleaned).strip()


class BNPApiClient:
    """Client for the public BNP (Banco Nacional de Precedentes) API."""

    def __init__(self, base_url: str = BNP_API_URL, timeout: int = 15) -> None:
        self.base_url = base_url
        self.timeout = timeout
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko)"
        )
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": user_agent,
        }

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=False,
    )
    def buscar(
        self,
        termo: str,
        orgaos: list[str] | None = None,
        tipos: list[str] | None = None,
        max_resultados: int = 5,
    ) -> list[dict[str, Any]]:
        """Search precedents in the BNP public API."""
        if not termo or not termo.strip():
            return []

        payload: dict[str, Any] = {
            "filtro": {
                "buscaGeral": termo.strip(),
                "todasPalavras": "",
                "quaisquerPalavras": "",
                "semPalavras": "",
                "trechoExato": "",
                "atualizacaoDesde": "",
                "atualizacaoAte": "",
                "cancelados": False,
                "ordenacao": "Text",
                "nr": "",
                "pagina": 1,
                "tamanhoPagina": min(max_resultados, 20),
                "orgaos": orgaos or ["STJ", "STF", "TJSP"],
                "tipos": tipos or ["RR", "RG", "SUM", "IRDR", "IAC"],
            }
        }

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            if response.status_code != 200:
                logger.warning(
                    "BNP API retornou status %s para termo '%s'",
                    response.status_code,
                    termo,
                )
                return []

            data = json.loads(response.content.decode("utf-8", errors="replace"))
            return data.get("resultados", [])
        except Exception as exc:
            logger.warning("Erro ao consultar BNP API para termo '%s': %s", termo, exc)
            return []


@dataclass(frozen=True)
class JurisprudenciaSyncReport:
    total: int
    inserted: int


def calculate_source_hash(data: dict[str, Any]) -> str:
    key_fields = {
        "tribunal_sigla": data.get("tribunal_sigla"),
        "identificador_precedente": data.get("identificador_precedente"),
        "assunto_codigo": data.get("assunto_codigo"),
        "titulo": data.get("titulo"),
    }
    serialized = json.dumps(key_fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _sanitize_term(term: str) -> str:
    """Sanitize subject name to optimize search queries."""
    clean = re.sub(r"[/\\()]", " ", term)
    tokens = [t.strip() for t in clean.split() if len(t.strip()) > 2]
    # Se começar por termos genéricos como DIREITO, foca nas próximas
    if tokens and tokens[0].upper() == "DIREITO" and len(tokens) > 1:
        tokens = tokens[1:]
    return " ".join(tokens[:4])


def fetch_and_save_precedents_for_subject(
    session_factory: SessionFactory,
    assunto_codigo: int,
    assunto_nome: str,
    client: BNPApiClient | None = None,
    max_precedentes: int = 3,
) -> int:
    """Fetch live precedents from BNP for a subject and persist them into Silver."""
    if client is None:
        client = BNPApiClient()

    search_query = _sanitize_term(assunto_nome)
    if not search_query:
        return 0

    results = client.buscar(search_query, max_resultados=max_precedentes)
    if not results:
        return 0

    inserted_count = 0
    with session_factory() as session:
        with session.begin():
            for r in results:
                tipo = r.get("tipo", "")
                nr = r.get("nr", "")
                identificador = (
                    f"{tipo} {nr}".strip() if nr else r.get("id", "Precedente")
                )
                orgao = r.get("orgao", "CNJ")

                tese_raw = r.get("tese") or ""
                questao_raw = r.get("questao") or ""
                tese = clean_html(tese_raw)
                questao = clean_html(questao_raw)

                titulo = (
                    questao[:250] if questao else f"{identificador} - {assunto_nome}"
                )
                ementa = questao if questao else tese

                if not tese and not ementa:
                    continue

                item_data = {
                    "tribunal_sigla": orgao,
                    "identificador_precedente": identificador,
                    "assunto_codigo": assunto_codigo,
                    "titulo": titulo,
                }
                source_hash = calculate_source_hash(item_data)

                existing = session.scalar(
                    select(SilverDataJudJurisprudencia).where(
                        SilverDataJudJurisprudencia.source_hash == source_hash
                    )
                )
                if existing is not None:
                    continue

                juris = SilverDataJudJurisprudencia(
                    id=uuid4(),
                    tribunal_sigla=orgao,
                    numero_processo=None,
                    identificador_precedente=identificador,
                    titulo=titulo,
                    ementa=ementa,
                    tese=tese,
                    relator=None,
                    data_julgamento=None,
                    assunto_codigo=assunto_codigo,
                    assunto_nome=assunto_nome,
                    source_hash=source_hash,
                )
                session.add(juris)
                inserted_count += 1

    return inserted_count


def sync_all_active_subjects(
    session_factory: SessionFactory,
    min_processos: int = 30,
) -> JurisprudenciaSyncReport:
    """Query high-volume subjects in Silver and fetch public precedents on-the-fly."""
    client = BNPApiClient()
    total_found = 0
    total_inserted = 0

    with session_factory() as session:
        query = text(
            """
            SELECT codigo, nome, COUNT(*) as qtd
            FROM silver.processo_assunto
            GROUP BY codigo, nome
            HAVING COUNT(*) >= :min_proc
            ORDER BY qtd DESC
            """
        )
        subjects = session.execute(query, {"min_proc": min_processos}).fetchall()

    for row in subjects:
        codigo = int(row.codigo)
        nome = str(row.nome)
        total_found += 1
        logger.info(
            "Buscando jurisprudência ao vivo no BNP para TPU %s - %s...", codigo, nome
        )
        ins = fetch_and_save_precedents_for_subject(
            session_factory=session_factory,
            assunto_codigo=codigo,
            assunto_nome=nome,
            client=client,
        )
        total_inserted += ins

    return JurisprudenciaSyncReport(total=total_found, inserted=total_inserted)


def main() -> None:
    factory = create_session_factory()
    report = sync_all_active_subjects(factory)
    msg = (
        f"Jurisprudência ao vivo (BNP/CNJ) sincronizada: {report.inserted} "
        f"novo(s) precedentes de {report.total} assuntos consultados."
    )
    print(msg)


if __name__ == "__main__":
    main()
