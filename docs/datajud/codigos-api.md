# Códigos da API Pública DataJud

Este documento explica os domínios codificados recebidos pela API Pública do
DataJud e identifica os códigos usados pelo DataLaw. Foi elaborado a partir do
[glossário da API](https://datajud-wiki.cnj.jus.br/api-publica/glossario/), do
[Modelo de Dados do DataJud](https://www.cnj.jus.br/wp-content/uploads/2020/07/XSD-DataJud-14_04_2020.pdf)
e do [Sistema de Gestão das Tabelas Processuais Unificadas (SGT)](https://www.cnj.jus.br/sgt/),
consultados em 24 de setembro de 2026.

## Visão geral

Os códigos da resposta não pertencem todos ao mesmo catálogo. Há domínios
fechados, que podem ser registrados diretamente nesta página, e domínios
versionados, mantidos pelo CNJ. Para estes últimos não é seguro congelar uma
lista no repositório: a TPU é atualizada continuamente pelo CNJ.

| Campo da API | Catálogo | Domínio fechado? | Onde obter o significado |
| --- | --- | --- | --- |
| `nivelSigilo` | Modelo de Dados do DataJud | Sim | Tabela abaixo. |
| `formato.codigo` | Modelo de Dados do DataJud | Sim | Tabela abaixo. |
| `sistema.codigo` | Modelo de Dados do DataJud | Sim | Tabela abaixo. |
| `grau` | Convenção de envio do DataJud | Sim | Tabela abaixo. |
| `tribunal` | Siglas dos tribunais | Não | [Endpoints/aliases da API](https://datajud-wiki.cnj.jus.br/api-publica/endpoints/). |
| `classe.codigo` | TPU — Classes | Não | [Consulta pública de classes](https://www.cnj.jus.br/sgt/consulta_publica_classes.php). |
| `assuntos[].codigo` | TPU — Assuntos | Não | [Consulta pública de assuntos](https://www.cnj.jus.br/sgt/consulta_publica_assuntos.php). |
| `movimentos[].codigo` | TPU — Movimentos | Não | [Consulta pública de movimentos](https://www.cnj.jus.br/sgt/consulta_publica_movimentos.php). |
| `complementosTabelados[].codigo` e `.valor` | TPU — Complementos de movimentos | Não | [Tabela de complementos](https://www.cnj.jus.br/sgt/gerenciar_complementos.php). |
| `orgaoJulgador.codigo` e `codigoOrgao` | Identificador local de serventia/vara | Não | Nome retornado no mesmo objeto e cadastro do tribunal de origem. |
| `codigoMunicipioIBGE` | IBGE — município | Não | [API de localidades do IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/municipios). |

## Domínios fechados

### Nível de sigilo (`nivelSigilo`)

| Código | Significado oficial |
| --- | --- |
| `0` | Público. Acessível a servidores do Judiciário e órgãos colaboradores, advogados e qualquer cidadão. |
| `1` | Segredo de justiça. Acessível a servidores do Judiciário, órgãos colaboradores e partes do processo. |
| `2` | Sigilo mínimo. Acessível a servidores do Judiciário e órgãos colaboradores. |
| `3` | Sigilo médio. Acessível a servidores do órgão em que o processo tramita, às partes que provocaram o incidente e a usuários expressamente incluídos. |
| `4` | Sigilo intenso. Acessível a classes qualificadas de servidores do órgão, às partes que provocaram o incidente e a usuários expressamente incluídos. |
| `5` | Sigilo absoluto. Acessível ao magistrado do órgão, aos usuários por ele indicados e às partes que provocaram o incidente. |

Na API Pública, processos sigilosos são resguardados. O valor deve ser tratado
como classificação de acesso, e não como indicador de conteúdo, prioridade ou
resultado processual.

### Formato do processo (`formato.codigo`)

| Código | Significado |
| --- | --- |
| `1` | Sistema/processo eletrônico. |
| `2` | Sistema/processo físico. |

Essa correspondência vem do campo `procEI` do Modelo de Dados do DataJud. Ao
consumir a API, mantenha também `formato.nome`, pois ele é a descrição devolvida
pelo índice.

### Sistema processual (`sistema.codigo`)

| Código | Sistema |
| --- | --- |
| `1` | PJe |
| `2` | Projudi |
| `3` | SAJ |
| `4` | EPROC |
| `5` | Apolo |
| `6` | Themis |
| `7` | Libra |
| `8` | Outros |

O código `8` também é o valor indicado pelo CNJ quando o processo tramita em
meio físico. Não use o código de sistema para inferir, sozinho, o formato do
processo; prefira `formato.codigo`.

### Grau de jurisdição (`grau`)

| Código | Significado |
| --- | --- |
| `Sup` | Tribunais Superiores. |
| `G2` | Segundo grau. |
| `G1` | Primeiro grau da justiça comum. |
| `TR` | Turmas Recursais. |
| `JE` | Juizados Especiais. |
| `TRU` | Turmas Regionais de Uniformização. |
| `TNU` | Turmas Nacionais de Uniformização. |

Os valores são siglas, não inteiros. Para filtros, preserve sua grafia tal como
for recebida da API.

## Códigos TPU: classes, assuntos e movimentos

As Tabelas Processuais Unificadas (TPU) padronizam classes, assuntos,
movimentações e documentos processuais em todo o Poder Judiciário. São
catálogos hierárquicos, extensos e sujeitos a alterações do CNJ. Portanto, não
existe uma enumeração estável e finita que possa ser reproduzida neste arquivo.

Para cada ocorrência retornada pelo DataJud, a própria API fornece a descrição
vigente junto ao código:

| Código | Campo com o significado no mesmo payload |
| --- | --- |
| `classe.codigo` | `classe.nome` |
| `assuntos[].codigo` | `assuntos[].nome` |
| `movimentos[].codigo` | `movimentos[].nome` |
| `movimentos[].complementosTabelados[].codigo` | `movimentos[].complementosTabelados[].descricao` |
| `movimentos[].complementosTabelados[].valor` | `movimentos[].complementosTabelados[].nome` |

Para uma consulta completa — incluindo hierarquia, glossário, norma, artigo,
abrangência por ramo de justiça e versões históricas — use o SGT nos links da
tabela inicial. O portal de TPU também disponibiliza tabelas em Excel/SQL e
consulta por API; ele é a fonte adequada para gerar uma dimensão local
versionada, se o projeto passar a necessitar disso.

### Códigos TPU empregados pelo DataLaw

O pipeline usa estes movimentos somente para selecionar processos concluídos
na carga histórica e incremental:

| Código | Nome TPU | Uso no DataLaw |
| --- | --- | --- |
| `22` | Baixa definitiva | Processo candidato à ingestão quando o movimento ocorreu na janela de seis meses. |
| `246` | Arquivamento definitivo | Processo candidato à ingestão quando o movimento ocorreu na janela de seis meses. |

Esses valores estão definidos em `COMPLETION_CODES` em
`src/data_law/ingestion/ingestion.py`. Eles não afirmam que todo processo com
um desses movimentos deve ser interpretado como decisão favorável, desfavorável
ou aderente a precedente; são somente o critério técnico atual de conclusão da
ingestão.

Como referência operacional, o SGT descreve o movimento `246` como envio ao
arquivo definitivo, sem expectativa de prosseguimento normal. Para retomar a
tramitação depois de arquivamento definitivo, o catálogo cita o movimento `849`
(Reativação); para retirada sem retomar o trâmite, cita `893`
(Desarquivamento). Esses códigos não são filtros do DataLaw.

## Códigos de complementos tabelados

Um complemento possui dois níveis de código:

```json
{
  "codigo": 47,
  "descricao": "classe_acao_controle_constitucionalidade_STF",
  "valor": 362,
  "nome": "ADC"
}
```

- `codigo` identifica **qual variável complementar** é usada pelo movimento.
- `valor` identifica **a opção escolhida** dentro daquela variável, quando ela
  for tabelada.
- `descricao` e `nome` são as descrições correspondentes e devem ser mantidas
  para auditoria e exibição.

O mesmo `valor` pode ter significado diferente em outra variável. Assim, uma
chave segura para uma dimensão de complementos é ao menos
`(codigo, valor)`, nunca apenas `valor`.

## Órgão julgador, município e tribunal

`orgaoJulgador.codigo` e `movimentos[].orgaoJulgador.codigoOrgao` identificam
uma serventia/vara na origem. Não são códigos TPU nem existe, no glossário da
API Pública, uma tabela nacional de conversão desses valores. Use o campo de
nome correspondente e a sigla do tribunal como contexto de identidade.

`orgaoJulgador.codigoMunicipioIBGE` é o código de município do IBGE. Armazene-o
como texto quando houver risco de formatação e faça a resolução pelo catálogo
oficial do IBGE, que é independente do catálogo de órgãos julgadores.

A sigla de `tribunal` identifica o índice/tribunal consultado. A relação de
siglas e aliases de endpoint é publicada na
[lista de endpoints da API Pública](https://datajud-wiki.cnj.jus.br/api-publica/endpoints/).
No escopo atual do DataLaw, o tribunal configurado é `TJSP`.

## Regras de implementação

- Para fatos históricos, guarde o par código/nome como recebido no payload:
  uma atualização posterior da TPU pode renomear, substituir ou desativar um
  item.
- Para filtros e agregações, prefira o código; para a interface, exiba o nome
  recebido e, quando necessário, complemente-o com o glossário do SGT.
- Antes de incluir códigos TPU novos como regra de negócio, registre a versão e
  a data de consulta do SGT e cubra a regra com testes.
- Para criar dimensões de classes, assuntos ou movimentos, obtenha a versão
  completa do SGT e registre sua data/versão; não faça uma tabela parcial a
  partir de exemplos de respostas da API.

## Fontes oficiais

- [Glossário de Dados — API Pública DataJud](https://datajud-wiki.cnj.jus.br/api-publica/glossario/)
- [Orientações gerais do DataJud — graus de jurisdição](https://www.cnj.jus.br/sistemas/datajud/orientacoes/)
- [Perguntas frequentes do DataJud — sistema e sigilo](https://www.cnj.jus.br/sistemas/datajud/perguntas-frequentes/)
- [Tabelas Processuais Unificadas — CNJ](https://www.cnj.jus.br/programas-e-acoes/tabela-processuais-unificadas/)
- [SGT — complementos de movimentos](https://www.cnj.jus.br/sgt/gerenciar_complementos.php)
- [API de localidades — IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/municipios)
