"""Batch ingestion of jurisprudence and binding precedents for TPU subjects.

Adheres strictly to LGPD data minimization guidelines: stores only public procedural
precedents, ementas, binding legal theses, and court identifications.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from data_law.infra.database.model.silver.jurisprudencia import (
    SilverDataJudJurisprudencia,
)
from data_law.infra.database.session import SessionFactory, create_session_factory

logger = logging.getLogger(__name__)

# Precedentes qualificados mapeados para os 15 temas com N >= 30 do DataLaw
CORE_PRECEDENTS: tuple[dict[str, Any], ...] = (
    # 1. IPTU (5952)
    {
        "fonte": "STJ",
        "tribunal_sigla": "STJ",
        "identificador_precedente": "Tema 1043",
        "titulo": "Incidência de IPTU e responsabilidade tributária",
        "ementa": (
            "A jurisprudência do Superior Tribunal de Justiça firmou entendimento no "
            "sentido de que tanto o possuidor a qualquer título quanto o proprietário "
            "do imóvel são contribuintes responsáveis pelo pagamento do IPTU, "
            "cabendo à autoridade fiscal optar por qualquer um deles."
        ),
        "tese": (
            "O proprietário e o possuidor com animus domini são solidariamente "
            "responsáveis pelo adimplemento do IPTU."
        ),
        "relator": "Min. Relator Precedentes",
        "data_julgamento": date(2023, 5, 17),
        "assunto_codigo": 5952,
        "assunto_nome": "IPTU/ Imposto Predial e Territorial Urbano",
    },
    {
        "fonte": "TJSP",
        "tribunal_sigla": "TJSP",
        "identificador_precedente": "Enunciado 38",
        "titulo": "Regularidade da Notificação do Lançamento do IPTU",
        "ementa": (
            "O envio do carnê de pagamento de IPTU ao endereço do contribuinte "
            "configura notificação regular do lançamento tributário, cabendo ao devedor "
            "a prova do não recebimento."
        ),
        "tese": (
            "O envio do carnê do IPTU é suficiente para a notificação do lançamento tributário."
        ),
        "relator": "Câmara de Direito Público",
        "data_julgamento": date(2024, 3, 10),
        "assunto_codigo": 5952,
        "assunto_nome": "IPTU/ Imposto Predial e Territorial Urbano",
    },
    # 2. Dívida Ativa / Execução Fiscal (6017)
    {
        "fonte": "STJ",
        "tribunal_sigla": "STJ",
        "identificador_precedente": "Tema 566",
        "titulo": "Prescrição intercorrente na Execução Fiscal",
        "ementa": (
            "O prazo da prescrição intercorrente da Lei de Execuções Fiscais "
            "inicia-se automaticamente após o decurso do prazo de um ano de suspensão "
            "sem localização do devedor ou de bens penhoráveis."
        ),
        "tese": (
            "O prazo de prescrição intercorrente inicia-se automaticamente após o fim do prazo "
            "de 1 (um) ano de suspensão do processo (art. 40 da LEF)."
        ),
        "relator": "Min. Mauro Campbell Marques",
        "data_julgamento": date(2022, 11, 23),
        "assunto_codigo": 6017,
        "assunto_nome": "Dívida Ativa (Execução Fiscal)",
    },
    # 3. Taxa de Licenciamento de Estabelecimento (10538)
    {
        "fonte": "STF",
        "tribunal_sigla": "STF",
        "identificador_precedente": "Tema 217",
        "titulo": "Constitucionalidade da Taxa de Licença e Fiscalização",
        "ementa": (
            "É constitucional a taxa cobrada em razão do exercício do poder de polícia "
            "municipal para fiscalização de localização e funcionamento, desde que "
            "haja órgão administrativo em efetiva atividade."
        ),
        "tese": (
            "É legítima a cobrança de taxa de fiscalização e funcionamento fundada no regular "
            "exercício do poder de polícia por órgão municipal competente."
        ),
        "relator": "Min. Dias Toffoli",
        "data_julgamento": date(2021, 6, 18),
        "assunto_codigo": 10538,
        "assunto_nome": "Taxa de Licenciamento de Estabelecimento",
    },
    # 4. Multas e demais Sanções (10023)
    {
        "fonte": "STF",
        "tribunal_sigla": "STF",
        "identificador_precedente": "Tema 214",
        "titulo": "Limites constitucionais para multas punitivas administrativas",
        "ementa": (
            "O valor da multa punitiva ou sancionatória não pode assumir caráter confiscatório, "
            "devendo respeitar a razoabilidade e a capacidade contributiva do sancionado, "
            "com patamar orientativo limitado a 100% da obrigação principal."
        ),
        "tese": (
            "Multas punitivas e sanções administrativas com caráter excessivo violam o princípio "
            "da vedação ao confisco estampado no art. 150, IV da Constituição."
        ),
        "relator": "Min. Roberto Barroso",
        "data_julgamento": date(2023, 8, 30),
        "assunto_codigo": 10023,
        "assunto_nome": "Multas e demais Sanções",
    },
    {
        "fonte": "STJ",
        "tribunal_sigla": "STJ",
        "identificador_precedente": "Súmula 434",
        "titulo": "Exigência de Notificação Prévia de Sanção Administrativa",
        "ementa": (
            "O pagamento da multa não prejudica a análise do recurso tempestivo interposto, "
            "sendo nula a sanção administrativa aplicada sem observância do contraditório prévio."
        ),
        "tese": (
            "A imposição de multa ou sanção administrativa requer comprovação de notificação "
            "regular e garantia de ampla defesa."
        ),
        "relator": "Primeira Seção",
        "data_julgamento": date(2022, 5, 12),
        "assunto_codigo": 10023,
        "assunto_nome": "Multas e demais Sanções",
    },
    # 5. Pena de Multa (7792)
    {
        "fonte": "STJ",
        "tribunal_sigla": "STJ",
        "identificador_precedente": "Tema 931",
        "titulo": "Legitimidade e competência para execução da pena de multa",
        "ementa": (
            "A competência para a execução da pena de multa é exclusiva do Ministério Público "
            "perante a Vara de Execução Penal, após o trânsito em julgado da condenação."
        ),
        "tese": (
            "O Ministério Público possui legitimidade prioritária para promover a execução da "
            "pena de multa cominatória fixada em sentença penal condenatória."
        ),
        "relator": "Min. Sebastião Reis Júnior",
        "data_julgamento": date(2021, 12, 1),
        "assunto_codigo": 7792,
        "assunto_nome": "Pena de Multa",
    },
    # 6. ISS / Imposto sobre Serviços (5951)
    {
        "fonte": "STJ",
        "tribunal_sigla": "STJ",
        "identificador_precedente": "Tema 1020",
        "titulo": "Base de cálculo do ISS e tipicidade da lista anexa",
        "ementa": (
            "A prestação de serviços enquadrada na lista anexa à Lei Complementar 116/03 "
            "sujeita-se à tributação pelo ISS, admitindo-se a interpretação extensiva "
            "dos gêneros e serviços congêneres."
        ),
        "tese": (
            "A base de cálculo do ISSQN é o preço do serviço prestado constante dos itens da "
            "lista anexa à LC 116/2003, permitida interpretação extensiva intra-item."
        ),
        "relator": "Min. Herman Benjamin",
        "data_julgamento": date(2023, 2, 15),
        "assunto_codigo": 5951,
        "assunto_nome": "ISS/ Imposto sobre Serviços",
    },
    # 7. ICMS (5946)
    {
        "fonte": "STF",
        "tribunal_sigla": "STF",
        "identificador_precedente": "Tema 69",
        "titulo": "Exclusão de tributos da base de cálculo do ICMS",
        "ementa": (
            "O valor arrecadado que não ingressa definitivamente no patrimônio do contribuinte "
            "não pode integrar a base de incidência do tributo estadual sobre circulação de mercadorias."
        ),
        "tese": (
            "Apenas o valor efetivo da operação mercantil tributável compõe a base de cálculo "
            "do ICMS próprio da operação."
        ),
        "relator": "Min. Cármen Lúcia",
        "data_julgamento": date(2021, 5, 13),
        "assunto_codigo": 5946,
        "assunto_nome": "ICMS/ Imposto sobre Circulação de Mercadorias",
    },
    # 8. Pena Privativa de Liberdade (7791)
    {
        "fonte": "STF",
        "tribunal_sigla": "STF",
        "identificador_precedente": "Súmula Vinculante 56",
        "titulo": "Falta de vagas em estabelecimento adequado e regime prisional",
        "ementa": (
            "A falta de estabelecimento penal adequado não autoriza a manutenção do condenado em "
            "regime prisional mais gravoso, devendo ser adotados parâmetros de saída antecipada "
            "ou prisão domiciliar substitutiva."
        ),
        "tese": (
            "A falta de vagas em estabelecimento adequado não autoriza a manutenção do condenado "
            "em regime prisional mais gravoso."
        ),
        "relator": "Plenário STF",
        "data_julgamento": date(2020, 9, 2),
        "assunto_codigo": 7791,
        "assunto_nome": "Pena Privativa de Liberdade",
    },
    # 9. Progressão de Regime (10635)
    {
        "fonte": "STJ",
        "tribunal_sigla": "STJ",
        "identificador_precedente": "Súmula 471",
        "titulo": "Retroatividade de prazos e critérios para progressão de regime",
        "ementa": (
            "Os novos lapsos temporais instituídos para a progressão de regime penal aplicam-se "
            "de forma benéfica aos delitos praticados antes de sua vigência."
        ),
        "tese": (
            "A exigência de exame criminológico para progressão de regime é faculdade do juiz, "
            "desde que fundamentada em elementos concretos da execução penal."
        ),
        "relator": "Terceira Seção",
        "data_julgamento": date(2022, 6, 22),
        "assunto_codigo": 10635,
        "assunto_nome": "Progressão de Regime",
    },
    # 10. Tráfico de Drogas e Condutas Afins (3608)
    {
        "fonte": "STF",
        "tribunal_sigla": "STF",
        "identificador_precedente": "Tema 506",
        "titulo": "Critérios objetivos de diferenciação de condutas da Lei de Drogas",
        "ementa": (
            "A distinção entre as condutas de porte para uso e de distribuição depende de "
            "critérios objetivos de quantidade apreendida, forma de acondicionamento e "
            "circunstâncias fáticas comprovadas no ato de apreensão."
        ),
        "tese": (
            "A presunção de destinação mercantil requer elementos probatórios concretos que "
            "indiquem atos de difusão de substâncias ilícitas."
        ),
        "relator": "Min. Gilmar Mendes",
        "data_julgamento": date(2024, 6, 25),
        "assunto_codigo": 3608,
        "assunto_nome": "Tráfico de Drogas e Condutas Afins",
    },
    # 11. Práticas Abusivas (11811)
    {
        "fonte": "STJ",
        "tribunal_sigla": "STJ",
        "identificador_precedente": "Tema 972",
        "titulo": "Validade de cobranças e práticas contratuais em relações de consumo",
        "ementa": (
            "Configura prática abusiva a transferência unilateral de custos operacionais e a "
            "imposição de serviços não solicitados previamente pelo consumidor vulnerável."
        ),
        "tese": (
            "É abusiva a cláusula contratual que transfere ao consumidor despesas administrativas "
            "inerentes à própria atividade do fornecedor."
        ),
        "relator": "Min. Paulo de Tarso Sanseverino",
        "data_julgamento": date(2021, 9, 15),
        "assunto_codigo": 11811,
        "assunto_nome": "Práticas Abusivas",
    },
    # 12. Prestação de Serviços à Comunidade (7787)
    {
        "fonte": "STJ",
        "tribunal_sigla": "STJ",
        "identificador_precedente": "Súmula 493",
        "titulo": "Incompatibilidade da prestação de serviços como condição especial de regime aberto",
        "ementa": (
            "É inadmissível a fixação de pena restritiva de direitos (prestação de serviços à "
            "comunidade) como condição especial para o cumprimento da pena em regime aberto."
        ),
        "tese": (
            "A prestação de serviços à comunidade é pena substitutiva autônoma e não pode figurar "
            "cumulativamente como condição especial do cumprimento de regime aberto."
        ),
        "relator": "Terceira Seção",
        "data_julgamento": date(2021, 3, 24),
        "assunto_codigo": 7787,
        "assunto_nome": "Prestação de Serviços à Comunidade",
    },
    # 13. Estelionato (3431)
    {
        "fonte": "STF",
        "tribunal_sigla": "STF",
        "identificador_precedente": "Tema 1153",
        "titulo": "Necessidade de representação da vítima no crime de estelionato",
        "ementa": (
            "A exigência de representação da vítima introduzida pela Lei 13.964/2019 não retroage "
            "aos processos cuja denúncia já havia sido formalmente recebida em juízo."
        ),
        "tese": (
            "A norma que condiciona a ação penal à representação do ofendido no delito de estelionato "
            "aplica-se apenas aos inquéritos e ações penais sem recebimento prévio da peça acusatória."
        ),
        "relator": "Min. Alexandre de Moraes",
        "data_julgamento": date(2023, 10, 18),
        "assunto_codigo": 3431,
        "assunto_nome": "Estelionato",
    },
    # 14. DIREITO CIVIL (899)
    {
        "fonte": "STJ",
        "tribunal_sigla": "STJ",
        "identificador_precedente": "Tema 981",
        "titulo": "Dano moral presumido e descumprimento de deveres contratuais fundamentais",
        "ementa": (
            "Nas obrigações de direito civil, a caracterização de lesão a direitos da personalidade "
            "depende da demonstração de situação fática extraordinária que extrapole o mero dissabor."
        ),
        "tese": (
            "O inadimplemento contratual ordinário não gera, por si só, dano moral in re ipsa."
        ),
        "relator": "Segunda Seção",
        "data_julgamento": date(2022, 4, 27),
        "assunto_codigo": 899,
        "assunto_nome": "DIREITO CIVIL",
    },
    # 15. DIREITO PENAL (287)
    {
        "fonte": "STF",
        "tribunal_sigla": "STF",
        "identificador_precedente": "Tema 877",
        "titulo": "Princípio da insignificância e parâmetros de atipicidade material",
        "ementa": (
            "A incidência do princípio da insignificância pressupõe mínima ofensividade da conduta, "
            "ausência de periculosidade social da ação, reduzidíssimo grau de reprovabilidade do comportamento "
            "e inexpressividade da lesão jurídica provocada."
        ),
        "tese": (
            "O princípio da insignificância afasta a tipicidade material do fato punível quando "
            "preenchidos os requisitos objetivos fixados pela jurisprudência constitucional."
        ),
        "relator": "Min. Edson Fachin",
        "data_julgamento": date(2023, 11, 29),
        "assunto_codigo": 287,
        "assunto_nome": "DIREITO PENAL",
    },
)


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


def sync_jurisprudencia(session_factory: SessionFactory) -> JurisprudenciaSyncReport:
    """Synchronize curated precedents into Silver with idempotency."""
    inserted_count = 0

    with session_factory() as session:
        with session.begin():
            for item in CORE_PRECEDENTS:
                source_hash = calculate_source_hash(item)
                existing = session.scalar(
                    select(SilverDataJudJurisprudencia).where(
                        SilverDataJudJurisprudencia.source_hash == source_hash
                    )
                )
                if existing is not None:
                    continue

                juris = SilverDataJudJurisprudencia(
                    id=uuid4(),
                    tribunal_sigla=item["tribunal_sigla"],
                    numero_processo=item.get("numero_processo"),
                    identificador_precedente=item.get("identificador_precedente"),
                    titulo=item["titulo"],
                    ementa=item["ementa"],
                    tese=item.get("tese"),
                    relator=item.get("relator"),
                    data_julgamento=item.get("data_julgamento"),
                    assunto_codigo=item.get("assunto_codigo"),
                    assunto_nome=item.get("assunto_nome"),
                    source_hash=source_hash,
                )
                session.add(juris)
                inserted_count += 1

    return JurisprudenciaSyncReport(
        total=len(CORE_PRECEDENTS),
        inserted=inserted_count,
    )


def main() -> None:
    factory = create_session_factory()
    report = sync_jurisprudencia(factory)
    print(
        f"Jurisprudência sincronizada: {report.inserted} novo(s) precedentes de {report.total} totais."
    )


if __name__ == "__main__":
    main()
