# Glossário de dados da API Pública DataJud

Este documento descreve os campos que podem compor o objeto de processo
retornado pela API Pública do DataJud. Ele se baseia no [Glossário de Dados da
API Pública](https://datajud-wiki.cnj.jus.br/api-publica/glossario/) do CNJ,
consultado em 24 de setembro de 2026.

O DataLaw atualmente consulta o endpoint do TJSP, mas o formato abaixo é o
contrato público comum para os índices dos tribunais. A API disponibiliza
**metadados de processos públicos**; não se deve presumir que todos os campos
estarão presentes em toda resposta ou tribunal.

## Como interpretar os tipos

Os tipos do glossário são mapeamentos de índice (Elasticsearch). Na resposta
JSON, devem ser tratados assim:

| Tipo do glossário | Representação no JSON | Uso recomendado no DataLaw |
| --- | --- | --- |
| `text/keyword` | `string` | Texto. `keyword` permite comparação/filtro exato; preservar como texto, inclusive números de processo e códigos identificadores. |
| `long` | `number` inteiro | Inteiro de 64 bits. Em Python, `int`; no PostgreSQL, `BIGINT` quando for necessário suportar toda a faixa. |
| `datetime` | `string` de data/hora | Data no formato que a API fornecer. Converter somente após validação; manter o valor bruto em Bronze. |
| `object {}` | objeto JSON | Estrutura aninhada com campos próprios. |
| `array []` | lista JSON | Coleção, possivelmente vazia, de objetos descritos nas linhas filhas. |

> `null`, campo ausente e valores fora do formato esperado não são definidos
> pelo glossário como tipos de domínio. Por isso, a ingestão deve tratá-los como
> dados ausentes/invalidáveis, sem descartar o payload bruto.

## Estrutura do processo (`_source`)

Cada ocorrência de pesquisa contém o objeto do processo em `hits.hits[*]._source`.
O exemplo a seguir é apenas estrutural — os valores não formam um registro real.

```json
{
  "id": "TJSP_7_G1_123456_00000000000000000000",
  "tribunal": "TJSP",
  "numeroProcesso": "00000000000000000000",
  "dataAjuizamento": "2026-01-15T00:00:00.000Z",
  "grau": "G1",
  "nivelSigilo": 0,
  "formato": { "codigo": 1, "nome": "Eletrônico" },
  "sistema": { "codigo": 1, "nome": "PJe" },
  "classe": { "codigo": 7, "nome": "Procedimento Comum Cível" },
  "assuntos": [{ "codigo": 7681, "nome": "DIREITO CIVIL" }],
  "orgaoJulgador": {
    "codigo": 123456,
    "nome": "Vara Exemplo",
    "codigoMunicipioIBGE": 3550308
  },
  "movimentos": [
    {
      "codigo": 26,
      "nome": "Distribuição",
      "dataHora": "2026-01-15T10:30:00.000Z",
      "complementosTabelados": [],
      "orgaoJulgador": { "codigoOrgao": 123456, "nomeOrgao": "Vara Exemplo" }
    }
  ]
}
```

### Identificação e capa processual

| Caminho | Tipo | Descrição e observações |
| --- | --- | --- |
| `id` | `text/keyword` | Identificador de origem do processo no DataJud. A chave é composta por `Tribunal_Classe_Grau_OrgaoJulgador_NumeroProcesso`. |
| `tribunal` | `text/keyword` | Sigla do tribunal, como `TJSP`, `STJ` ou `STF`. |
| `numeroProcesso` | `text/keyword` | Numeração Única CNJ sem formatação. Não converter para número: zeros à esquerda são significativos. |
| `dataAjuizamento` | `datetime` | Data de ajuizamento na capa do processo. |
| `grau` | `text/keyword` | Instância/grau de jurisdição, por exemplo `G1`, `G2` ou `JE`. Os valores efetivamente disponíveis dependem do tribunal. |
| `nivelSigilo` | `long` | Nível de sigilo informado para o processo. O glossário define o tipo, mas não enumera valores permitidos; não inferir significado sem consultar a regra vigente do CNJ. |

### Formato e sistema de origem

| Caminho | Tipo | Descrição |
| --- | --- | --- |
| `formato` | `object {}` | Identifica se o processo é físico ou eletrônico. |
| `formato.codigo` | `long` | Código de identificação do formato. |
| `formato.nome` | `text/keyword` | Descrição do formato, como físico ou eletrônico. |
| `sistema` | `object {}` | Sistema processual de origem no tribunal. |
| `sistema.codigo` | `long` | Código do sistema processual. |
| `sistema.nome` | `text/keyword` | Descrição do sistema processual. |

### Classificação e assuntos (TPU)

TPU significa Tabelas Processuais Unificadas do CNJ. Códigos e nomes devem ser
consumidos em conjunto: o código é a chave de classificação e o nome é a
descrição disponibilizada pela fonte.

| Caminho | Tipo | Descrição |
| --- | --- | --- |
| `classe` | `object {}` | Classe processual conforme a TPU. |
| `classe.codigo` | `long` | Código da classe processual. |
| `classe.nome` | `text/keyword` | Nome/descrição da classe processual. |
| `assuntos` | `array []` | Lista de assuntos do processo conforme a TPU. |
| `assuntos[].codigo` | `long` | Código de um assunto. |
| `assuntos[].nome` | `text/keyword` | Nome/descrição de um assunto. |

### Órgão julgador atual

| Caminho | Tipo | Descrição |
| --- | --- | --- |
| `orgaoJulgador` | `object {}` | Órgão julgador atual do processo. |
| `orgaoJulgador.codigo` | `long` | Código da serventia ou vara atual. |
| `orgaoJulgador.nome` | `text/keyword` | Nome da serventia ou vara. |
| `orgaoJulgador.codigoMunicipioIBGE` | `long` | Código IBGE do município do órgão julgador. |

### Movimentos processuais

`movimentos` é uma lista. Cada item representa uma movimentação processual e
tem os seguintes atributos:

| Caminho | Tipo | Descrição |
| --- | --- | --- |
| `movimentos` | `array []` | Lista de movimentos processuais. |
| `movimentos[].codigo` | `long` | Código da movimentação conforme a TPU. |
| `movimentos[].nome` | `text/keyword` | Descrição da movimentação. |
| `movimentos[].dataHora` | `datetime` | Data e hora em que ocorreu a movimentação. |
| `movimentos[].complementosTabelados` | `array []` | Lista de complementos tabelados associados ao movimento. |
| `movimentos[].complementosTabelados[].codigo` | `long` | Código da variável de movimento tabelado. |
| `movimentos[].complementosTabelados[].descricao` | `text/keyword` | Descrição da variável de movimento tabelado. |
| `movimentos[].complementosTabelados[].valor` | `long` | Código do complemento tabelado. |
| `movimentos[].complementosTabelados[].nome` | `text/keyword` | Descrição do complemento tabelado. |
| `movimentos[].orgaoJulgador` | `object {}` | Órgão julgador associado ao movimento. |
| `movimentos[].orgaoJulgador.codigoOrgao` | `long` | Código da serventia ou vara no movimento. |
| `movimentos[].orgaoJulgador.nomeOrgao` | `text/keyword` | Nome da serventia ou vara no movimento. |

### Campos internos do índice

Estes campos constam no glossário, mas são usados para controle interno do
DataJud. Eles não são atributos de negócio da capa do processo.

| Caminho | Tipo | Descrição |
| --- | --- | --- |
| `dataHoraUltimaAtualizacao` | `datetime` | Milissegundos do atributo `millisInsercao` da origem do dado. Pode ser usado para controle de atualização, não como data de movimentação. |
| `@timestamp` | `datetime` | Momento da atualização do documento no índice. |

## Tratamento no DataLaw

A tabela abaixo delimita o que é preservado da API e o que já foi normalizado
no pipeline atual. O payload completo nunca é perdido: ele é armazenado como
JSONB em `bronze.datajud_extract.payload`.

| Campo da API | Destino atual | Tratamento |
| --- | --- | --- |
| `id` | `bronze.datajud_extract.datajud_id`; `silver.processo.datajud_id` | Identificador textual. |
| `tribunal` | `bronze.datajud_extract.tribunal_sigla`; `silver.processo.tribunal_sigla` | A sigla vem da configuração do tribunal consultado. |
| `numeroProcesso`, `grau`, `nivelSigilo`, `dataAjuizamento`, `dataHoraUltimaAtualizacao` | `silver.processo` | Normalizados como texto, inteiro, data ou timestamp. Datas inválidas resultam em `NULL` e aviso; o bruto é preservado em Bronze. |
| `classe.*`, `formato.*`, `sistema.*`, `orgaoJulgador.*` | `silver.processo` | Campos de código/nome normalizados. Os códigos de órgão são preservados como texto na Silver, evitando perda de formatação ou incompatibilidade de origem. |
| `movimentos[]` | `silver.movimento` | Um registro por objeto de movimento distinto; duplicatas idênticas são consolidadas por hash. |
| `movimentos[].complementosTabelados` | `silver.movimento.complementos_tabelados` | Mantido em JSONB. |
| `assuntos[]`, `@timestamp` e campos futuros | Somente `bronze.datajud_extract.payload` | Preservados no payload bruto; ainda não têm tabela/colunas normalizadas na Silver. |

## Regras práticas para consumidores

- Use `id` e `tribunal` para identidade da origem; não use apenas
  `numeroProcesso` como chave técnica entre índices.
- Trate `numeroProcesso`, siglas e códigos de identificação como texto quando
  houver qualquer risco de zero à esquerda ou formatação variável.
- Não deduza o desfecho do processo apenas pelo último item da lista de
  movimentos. A interpretação depende dos códigos TPU e das regras de negócio
  adotadas pelo projeto.
- Prefira os códigos TPU para filtros, agregações e integrações; os nomes são
  descrições que podem demandar padronização entre fontes.
- Mantenha o JSON original para auditoria, reprocessamento e absorção de novos
  atributos fornecidos pela API.

## Fontes oficiais

- [Glossário de Dados — API Pública DataJud](https://datajud-wiki.cnj.jus.br/api-publica/glossario/)
- [API Pública — Portal CNJ](https://www.cnj.jus.br/sistemas/datajud/api-publica/)
- [Endpoints e aliases dos tribunais — Datajud-Wiki](https://datajud-wiki.cnj.jus.br/api-publica/endpoints/)
- [Orientações gerais do DataJud — Portal CNJ](https://www.cnj.jus.br/sistemas/datajud/orientacoes/)
