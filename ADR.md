# ADR — Estado atual dos processos DataJud na Bronze

## Contexto

Uma resposta da API DataJud contém vários processos em `hits.hits`. O mesmo
processo pode ser devolvido novamente em extrações futuras, com novos
movimentos ou qualquer outro campo atualizado.

## Decisão

`bronze.datajud_extract` guarda uma linha por processo e tribunal:

- `id` é a chave técnica UUID;
- `(tribunal_sigla, datajud_id)` é a chave de negócio única;
- `payload` contém o objeto `_source` completo do processo;
- `payload_hash` é o SHA-256 da serialização JSON canônica do payload;
- `source_file` aponta para o último JSON raw que produziu aquele estado.

A carga usa um `INSERT ... ON CONFLICT ... DO UPDATE` condicionado a
`payload_hash IS DISTINCT FROM`. Assim, payload idêntico não gera escrita;
qualquer alteração no `_source` substitui o payload atual.

## Consequências

- A tabela representa apenas o estado mais recente de cada processo, sem
  histórico de versões no banco.
- Os arquivos em `data/raw` preservam as respostas originais e permitem
  auditoria ou reprocessamento.
- Novos tribunais precisam de uma entrada explícita no mapa de metadados do
  processador.
- A unicidade por arquivo não é usada: um arquivo pode conter muitos processos
  e um processo pode aparecer em muitos arquivos.

## Alternativas descartadas

- Uma linha por arquivo: não permite detectar mudanças por processo.
- Atualizar somente quando a quantidade de movimentos cresce: ignoraria
  correções e alterações relevantes em outros campos.
- Manter todas as versões do payload na mesma tabela: não atende ao requisito
  atual de manter apenas o estado mais recente.
