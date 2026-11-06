# Parecer técnico de engenharia de dados — VM simples

**Tipo de documento:** avaliação arquitetural (brownfield) e plano de evolução.
**Escopo avaliado:** implementação versionada em 23/09/2026: DataJud/TJSP, camadas Raw, Bronze e Silver.
**Objetivo:** minimizar CPU, RAM, I/O e espaço em disco sem perder rastreabilidade nem a capacidade de retomar cargas.

## Resumo executivo

A arquitetura tem uma base adequada para começar em uma VM pequena: PostgreSQL único, arquivos Raw comprimidos e imutáveis, `upsert` condicional por hash, janela de sobreposição de 48 horas e Silver SCD tipo 1. Ela evita recalcular registros sem alteração e não introduz componentes pesados desnecessários.

O resultado ponderado é **61/100 — utilizável para o piloto, mas precisa de correções antes de ampliar o histórico ou colocar uma rotina diária sem supervisão**. A maior preocupação não é a escolha do PostgreSQL, mas a consistência entre o filtro de elegibilidade, o conteúdo guardado no Raw e o reprocessamento. Hoje, um `bronze-load` pode carregar para Bronze processos que a ingestão normal havia excluído. Também não há retenção, catálogo nem controle de execução do Raw; assim, o disco será o primeiro limite da VM.

Não foram medidos tempos ou tamanho do banco nesta avaliação: a suíte passou com 12 testes e 1 integração ignorada por não haver `DATABASE_URL`. As notas representam a leitura do código e dos arquivos locais, não um benchmark de produção.

## Critério e resultado ponderado

Cada eixo recebe uma nota de 0 a 10 e um peso proporcional ao seu impacto na VM e na confiabilidade do dado. A nota final é a soma de `nota × peso`.

| Eixo | Peso | Nota | Pontos | Leitura curta |
| --- | ---: | ---: | ---: | --- |
| Estratégia de processamento | 20% | 7,0 | 14,0 | Incremental e idempotente; ainda processa e transaciona registro a registro. |
| Estratégia de armazenamento | 20% | 6,0 | 12,0 | Gzip e partição ajudam; há duplicação Raw/JSONB e não há ciclo de vida do disco. |
| Estratégia de reprocessamento | 15% | 4,0 | 6,0 | Retomável na Silver, mas o recarregamento Raw altera o escopo elegível. |
| Estratégia de ingestão | 15% | 7,0 | 10,5 | Paginação segura, retry e checkpoint após Silver; falta controle de execução concorrente. |
| Estratégia de reingestão | 10% | 5,0 | 5,0 | Reconsulta incremental é boa, porém não há modo de reingestão por período/tribunal nem retenção. |
| Modelagem Bronze | 10% | 6,5 | 6,5 | Bom estado corrente e linhagem; não é Bronze histórico e faltam índices operacionais. |
| Modelagem Silver | 10% | 7,0 | 7,0 | Modelo enxuto para processos e movimentos; ainda insuficiente para o analítico previsto. |
| **Total** | **100%** |  | **61,0 / 100** |  |

### Escala de interpretação

- **8–10:** adequado à VM simples no escopo atual.
- **6–7,9:** adequado com acompanhamento e melhorias pontuais.
- **4–5,9:** risco operacional ou de qualidade antes de crescer.
- **0–3,9:** corrigir antes de confiar em rotina automática.

## Estado observado

```text
DataJud API
  -> Raw: páginas JSON completas, gzip, por data e run_id
  -> Bronze: estado corrente de cada processo elegível, JSONB + hash
  -> Silver: processo e movimentos normalizados, estado corrente (SCD 1)
```

Há aproximadamente **40 MB de `data/` local**, com **111 arquivos `.json.gz`** e **7 arquivos JSON sem compressão**. É um volume pequeno, mas já demonstra a coexistência de dois padrões de Raw. O banco em Docker usa um volume sem limite de tamanho e a aplicação não define política de retenção, backup ou `VACUUM/ANALYZE`.

## Avaliação por eixo

### 1. Estratégia de processamento — 7,0/10 (peso 20%)

**Pontos fortes**

- O hash SHA-256 de JSON canônico evita `UPDATE` em Bronze quando o payload não mudou.
- A Silver seleciona somente processos Bronze ausentes ou com hash diferente e sincroniza cada processo e seus movimentos em uma transação.
- O lote lógico de Silver limita a busca a 500 pendências e não requer Spark, DataFrame ou um segundo motor de processamento.
- Datas inválidas e movimentos inválidos não interrompem toda a carga; o payload original permanece disponível.

**Limitações para uma VM pequena**

- Bronze faz um `INSERT ... ON CONFLICT` por processo. Silver abre uma sessão/transação, consulta os movimentos e emite operações ORM para cada processo alterado. Em um backfill grande, isso amplifica round-trips, WAL e CPU do PostgreSQL.
- Cada página é descomprimida e materializada integralmente em memória; depois seus `_source` são reunidos novamente em uma lista. O tamanho de página é fixo em 500, sem configuração operacional.
- A busca por pendências na Silver é um `OUTER JOIN` sobre toda Bronze a cada execução. Conforme Bronze cresce, a maior parte do trabalho diário será descobrir que nada mudou.
- Avisos de qualidade vão apenas para `stdout`; após a execução não há contagem por regra, amostra de erro ou fila de quarentena.

**Decisão recomendada:** manter Python + PostgreSQL, mas trocar o processamento por processo por operações em lote nas cargas grandes. Primeiro, tornar `PAGE_SIZE` e `batch_size` configuráveis por ambiente (por exemplo, 100–250 em VM de 2 GB). Depois, usar `executemany`/upsert em lote em Bronze e carregar movimentos por conjunto. Não introduzir Spark, Kafka ou Airflow neste estágio.

### 2. Estratégia de armazenamento — 6,0/10 (peso 20%)

**Pontos fortes**

- Raw é comprimido (`gzip`, nível 6), particionado por tribunal, data de ingestão e `run_id`, e gravado de forma atômica via arquivo temporário seguido de `replace`.
- Bronze usa `JSONB`, preserva o payload de origem e evita gravar uma cópia nova se o conteúdo for idêntico.
- Silver mantém apenas o estado corrente e normaliza os campos mais consultados, o que é apropriado para consultas operacionais pequenas.

**Limitações e riscos**

- O Raw grava a **resposta inteira da API antes do filtro de elegibilidade**. Logo, guarda processos que não entrarão na Bronze no fluxo normal. Isso contradiz a documentação atual, que afirma que Raw contém somente processos selecionados.
- Há três cópias parciais do mesmo dado: página Raw completa, payload JSONB em Bronze e projeção/movimentos em Silver. É uma troca aceitável em pequeno volume, mas sem retenção o Raw cresce indefinidamente.
- Não há manifesto de arquivos (tamanho, SHA-256, quantidade de hits, status, versão do filtro) nem política de expurgo/arquivamento. Não é possível saber de forma confiável o que pode ser removido nem auditar rapidamente um arquivo corrompido.
- `payload` e `complementos_tabelados` não têm índices GIN — decisão correta enquanto não houver filtro por JSONB. Criar GIN agora aumentaria disco e custo de escrita sem benefício demonstrado.

**Decisão recomendada:** manter Raw gzip como fonte de auditoria, mas registrar um catálogo de arquivos e definir ciclo de vida. Para a VM, uma política inicial prudente é reter no disco local os últimos 30 ou 90 dias, gerar backup compactado verificável dos demais arquivos para um volume externo/objeto compatível com S3 e somente então removê-los localmente. Se não existir armazenamento externo, explicitar o limite de disco e alertar antes de 80% de uso; não apagar Raw automaticamente.

### 3. Estratégia de reprocessamento — 4,0/10 (peso 15%)

**Pontos fortes**

- `silver-load` é idempotente e retoma corretamente: processos cujo `source_payload_hash` já coincide são ignorados.
- A transação por processo evita que uma atualização deixe processo e movimentos parcialmente sincronizados.
- Arquivos Raw imutáveis permitem reconstrução, desde que se preserve o mesmo critério de seleção.

**Problema crítico de escopo (P0)**

Na ingestão normal, a API salva uma página Raw e calcula `included_ids`; somente esses IDs são enviados para `process_raw_file`. Já `bronze-load` chama `process_raw_directory`, que não recebe nem reconstrói `included_ids` e, portanto, faz upsert de **todos** os `hits.hits` dos arquivos Raw. Como o arquivo contém a resposta inteira, um reprocessamento pode inserir em Bronze/Silver processos fora da regra de conclusão usada no histórico e no incremental.

Isso compromete a reprodutibilidade e pode alterar indicadores apenas porque foi executado um comando de recuperação.

**Correção mínima antes de usar `bronze-load`:** escolher e persistir uma destas opções por página:

1. guardar no Raw apenas os `_source` elegíveis, preservando também a resposta original em armazenamento de auditoria; ou
2. manter a página integral, mas gravar em um manifesto os `included_datajud_ids`, a versão da regra e as janelas aplicadas, e obrigar o reprocessador a usá-los; ou
3. tornar o filtro uma regra pura, versionada e reexecutável, com todos os parâmetros do run registrados. Esta opção é útil, mas sozinha não protege contra mudanças futuras de código.

Para uma VM simples, a opção 2 é a mais econômica: uma tabela/arquivo de manifesto pequeno, por página, evita duplicação de payload e preserva exatamente a decisão original.

**Outra melhoria:** oferecer reprocessamento seletivo por `run_id`, intervalo de datas e tribunal. O comando atual percorre todo `data/raw`, o que transforma uma correção pontual em varredura completa de disco e banco.

### 4. Estratégia de ingestão — 7,0/10 (peso 15%)

**Pontos fortes**

- Usa `search_after` com ordenação estável por `@timestamp` e `id.keyword`, evitando paginação baseada em offset.
- Usa timeout de 90 segundos e retry exponencial para falhas HTTP transitórias.
- A carga histórica limita o escopo a seis meses e aos códigos de conclusão 22/246; a incremental reconsulta 48 horas, reduzindo perda por atraso/atualização tardia.
- O checkpoint só é salvo depois que Bronze e Silver terminam, evitando declarar a execução concluída quando a Silver falhou.

**Limitações**

- Não há tabela de execução (`run`) com início/fim, cursor, parâmetros, páginas, contagens, erro e versão de código. Se a VM cair na página 80, o reinício cria um novo `run_id` e reconsulta tudo desde o começo.
- Não há bloqueio de execução. Dois cron jobs simultâneos podem fazer a mesma reingestão e avançar o checkpoint fora de ordem. Os hashes reduzem duplicidade de dados, mas não a duplicidade de API, Raw e carga.
- A filtragem é feita depois de baixar e persistir cada página inteira. É correta para validar a condição no mesmo movimento, porém o custo de disco é pago antes da seleção.
- A resposta marcada como `timed_out` falha corretamente, mas não há métrica nem alerta persistido para retries esgotados e respostas inválidas.

**Decisão recomendada:** criar uma tabela pequena de controle, por exemplo `control.ingestion_run` e `control.raw_file`, e usar `pg_try_advisory_lock` (ou lock file) para garantir uma execução por tribunal. Registrar cursor e página após cada confirmação possibilita retomar o mesmo run sem nova consulta. Esse controle custa pouco e é muito mais valioso que adicionar um orquestrador nesta fase.

### 5. Estratégia de reingestão — 5,0/10 (peso 10%)

**Pontos fortes**

- A reingestão diária consulta `@timestamp` desde `checkpoint - 48h` e também atualiza IDs já existentes na Bronze que reaparecem na resposta.
- A operação é idempotente quanto ao estado final: payload igual não provoca escrita nem transformação adicional.

**Limitações**

- Não há CLI para reingestar explicitamente um tribunal e uma janela escolhida (por exemplo, “TJSP, 01–15/08”), nem opção segura de repetir somente um run com falha.
- Reexecutar `--full` sempre baixa novamente seis meses e cria novos arquivos Raw, mesmo que não haja mudança. Isso é caro em banda e disco.
- A janela fixa de 48 horas é uma hipótese não monitorada. Sem medir a defasagem entre evento e `@timestamp`, não há evidência de que ela cubra atualizações tardias.

**Decisão recomendada:** expor parâmetros `--tribunal`, `--from`, `--to`, `--resume-run` e `--overlap-hours`, todos registrados no run. Manter 48 horas inicialmente, e avaliar mensalmente a maior diferença observada entre `dataHoraUltimaAtualizacao` e o momento de coleta para ajustar a sobreposição baseada em evidência.

### 6. Modelagem da Bronze — 6,5/10 (peso 10%)

**Adequação atual**

`bronze.datajud_extract` tem grão claro: um estado atual por `(tribunal_sigla, datajud_id)`. `payload_hash`, `source_file` e `extracted_at` dão boa linhagem para o último estado. A restrição única atende ao upsert e o JSONB absorve evolução do contrato DataJud sem migração imediata.

**Ressalvas**

- Pelo uso convencional de medallion, Bronze tende a ser append-only e histórico. Aqui ela é um **espelho operacional de estado corrente**; o histórico está no filesystem Raw. A decisão é válida para uma VM simples, mas deve ser nomeada e documentada assim para evitar expectativa errada de histórico no banco.
- `source_file` só aponta para o último arquivo. Não há relação N:N entre processo e todas as páginas/runs que o observaram.
- Não há índices específicos para a busca de pendências Silver ou para operações administrativas por `extracted_at`; a chave única existente serve à busca por negócio, não a todos os fluxos operacionais.
- Não há estado explícito de pendência/erro de transformação. A Silver descobre mudanças por comparação de hash em leitura.

**Modelo recomendado, sem duplicar histórico no PostgreSQL:** manter a tabela atual e acrescentar `ingestion_run_id`, `updated_at`, `silver_status`/`silver_processed_hash` (ou uma fila de pendências) e índices parciais da fila. Incluir uma tabela de manifesto Raw com `path`, hash do arquivo, bytes compactados, número de hits, IDs elegíveis, regra/versão e status. Isso permite reprocessar exatamente o conjunto correto e elimina a varredura completa para encontrar pendências.

### 7. Modelagem da Silver — 7,0/10 (peso 10%)

**Adequação atual**

O grão de `silver.processo` é um processo DataJud corrente e o de `silver.movimento` é um movimento corrente deduplicado pelo hash do objeto original. A chave única de processo e o índice `(processo_id, data_hora)` sustentam o fluxo atual com pouco armazenamento. Colunas de linhagem (`bronze_extract_id`, hashes, arquivo e timestamps) são uma boa escolha.

**Limitações**

- É uma tabela de projeção parcialmente desnormalizada, não um modelo dimensional analítico. Para os requisitos futuros faltam, entre outros, relação processo–assunto, dimensões conformadas de tribunal/classe/órgão, tema/classificação, decisão, fonte/confiabilidade e calendário de indicadores.
- `movimento` não mantém posição original nem chave estável de evento; uma correção em qualquer campo muda o hash, removendo a linha anterior e inserindo outra. Para SCD1 isso é aceitável, mas não permite auditoria de evento nem associação estável posterior.
- A deduplicação de movimentos idênticos pode eliminar eventos legítimos se a fonte realmente repetir o mesmo objeto. Deve ser validada contra regras DataJud antes de calcular volume de movimentações.
- Faltam índices para as próprias consultas existentes: `list_processes` filtra `tribunal_sigla` e ordena por `data_hora_ultima_atualizacao`, mas não há índice composto; filtros por classe, órgão e período futuro também exigirão índices orientados aos padrões reais de consulta.
- `complementos_tabelados` em JSONB é aceitável enquanto não é filtro. Quando um complemento virar dimensão analítica, deve ser extraído para uma relação própria, não indexado genericamente em JSONB.

**Decisão recomendada:** não antecipar um star schema completo agora. Primeiro extrair `assuntos` e uma tabela de relacionamento `processo_assunto` quando o filtro por tema entrar no escopo. Criar Gold somente para métricas definidas e usar dimensões pequenas/conformadas. Manter Silver como estado atual e construir fatos Gold incrementais, em vez de consultar JSONB da Bronze para dashboards.

## Inconsistência documental e operacional

Há dois caminhos de DDL no repositório: as migrations Alembic usadas pela aplicação e os scripts `sql/DatabaseCreation.sql`, `sql/load_bronze.sh` e `sql/load_silver.sh`, que descrevem outro modelo (por exemplo, `extract_id`, `datajud_hit` e dimensões que não existem nas migrations correntes). Eles não são compatíveis com o fluxo Python atual.

**Ação recomendada:** declarar Alembic como única fonte de verdade e mover os scripts SQL antigos para `sql/legacy/` com aviso explícito, ou atualizá-los para o mesmo schema. Em uma VM simples, duas definições concorrentes de banco são um risco maior que a falta de uma ferramenta de orquestração.

## Plano priorizado

| Prioridade | Ação | Benefício principal | Esforço relativo |
| --- | --- | --- | --- |
| P0 | Persistir manifesto de elegibilidade por página/run e fazer `bronze-load` respeitá-lo. Bloquear o comando até a correção. | Reprocessamento reproduzível; evita dados fora do escopo. | Médio |
| P0 | Criar `ingestion_run`/`raw_file`, registrar checkpoint/cursor por página e aplicar lock por tribunal. | Retomada após falha e evita execuções concorrentes. | Médio |
| P1 | Definir retenção, backup e alerta de disco para Raw e volume PostgreSQL. | Evita indisponibilidade por disco cheio. | Baixo–médio |
| P1 | Marcar Bronze alterada como pendente de Silver e indexar a fila. | Elimina varredura completa de Bronze a cada rotina. | Médio |
| P1 | Tornar tamanhos de página/lote configuráveis e fazer upserts em lote. | Menos RAM, CPU, WAL e tempo de backfill. | Médio |
| P1 | Unificar migrations e scripts SQL/documentação. | Evita criação de schema incorreto. | Baixo |
| P2 | Criar registro persistente de qualidade/quarentena. | Auditoria e correção de payloads inválidos. | Médio |
| P2 | Adicionar `processo_assunto` e índices guiados por consultas reais. | Prepara filtros e Gold sem inflar JSONB. | Médio |

## Arquitetura-alvo mínima para a VM

```text
cron/systemd (uma execução por tribunal, com lock)
  -> DataJud API
  -> Raw gzip + manifesto/checksum
  -> PostgreSQL Bronze (estado atual + fila de pendências)
  -> PostgreSQL Silver (estado atual normalizado)
  -> Gold incremental, somente quando a métrica estiver definida

backup periódico: Raw arquivado + pg_dump testado
observabilidade mínima: tabela de runs, logs estruturados e alerta de disco
```

Esta proposta preserva a stack atual e cabe em uma única VM. DuckDB, Polars, fila externa, Airflow, Kafka e cluster só devem ser considerados quando houver evidência de que os lotes SQL/Python e o PostgreSQL ajustados não atendem à janela diária ou ao volume de histórico.

## Checklist de aceite antes da rotina diária

- [ ] Reprocessar um `run_id` produz exatamente o mesmo conjunto de IDs elegíveis da execução original.
- [ ] Interromper a carga em uma página e retomá-la sem consultar novamente páginas já confirmadas.
- [ ] Duas execuções simultâneas para TJSP não avançam checkpoint nem gravam Raw em paralelo.
- [ ] Há alerta antes de o disco chegar a 80% e um backup restaurável testado.
- [ ] `silver-load` busca somente processos marcados como pendentes; não faz varredura integral em rotina normal.
- [ ] Consultas de uso real possuem `EXPLAIN (ANALYZE, BUFFERS)` registrado antes de novos índices.
- [ ] A documentação distingue explicitamente Raw histórico, Bronze de estado corrente e Silver SCD1.

## Evidências principais no código

- `src/data_law/ingestion/ingestion.py`: paginação, retry, filtro, checkpoint e persistência Raw antes de `included_ids`.
- `src/data_law/ingestion/bronze.py`: upsert por hash e reprocessamento sem filtro de elegibilidade.
- `src/data_law/ingestion/storage.py`: gzip, partição e escrita atômica.
- `src/data_law/transformation/silver.py`: seleção de pendências, transação por processo e SCD1.
- `migration/versions/20260921_04_create_silver_process_and_movement.py`: grãos, chaves e índices efetivos da Silver.
- `sql/DatabaseCreation.sql` e `sql/load_*.sh`: DDL/carga legados que divergem do schema Alembic atual.
