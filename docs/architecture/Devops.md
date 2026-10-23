# DevOps — DataLaw

Documentação completa do processo de integração contínua (CI) e entrega contínua (CD) do projeto DataLaw.

---

## Visão Geral da Arquitetura

O DataLaw é composto por dois serviços independentes, cada um hospedado em sua própria VM na Azure:

| Serviço | Tecnologia | VM | Porta |
|---|---|---|---|
| **Frontend** | Java 21 / Spring Boot (JAR) | `AZURE_FRONTEND_VM_HOST` | `8080` |
| **Backend** | Python 3.12 / FastAPI (uv) | `AZURE_VM_HOST` | — |

O banco de dados **PostgreSQL 18** roda na VM do backend, gerenciado via Docker.

---

## Fluxo Completo do Pipeline

O pipeline é disparado automaticamente pelo GitHub Actions a cada `push` ou `pull_request` direcionado à branch `main`.

```
 Desenvolvedor
      │
      │  git push / pull_request → main
      ▼
┌─────────────────────────────────┐
│         JOB 1: test (CI)        │  ← roda sempre (push + PR)
│  lint → format → unit tests →  │
│  migrations → integration tests │
└────────────────┬────────────────┘
                 │  só se passou E é push para main
        ┌────────┴────────┐
        ▼                 ▼
┌───────────────┐  ┌──────────────────┐
│  JOB 2: CD    │  │    JOB 3: CD     │
│   Frontend    │  │     Backend      │
│ (Maven → JAR) │  │ (uv → systemd)   │
└───────────────┘  └──────────────────┘
```

> **Regra de ouro:** nenhum deploy acontece se qualquer teste falhar.

---

## JOB 1 — Testes Automatizados (CI)

**Gatilho:** todo `push` e `pull_request` para `main`  
**Arquivo:** [`.github/workflows/deploy.yml`](file:///media/jackson/DEV/DEV/ProjetoAPI/DataLaw/.github/workflows/deploy.yml)

### Serviço de banco para testes

O GitHub Actions sobe um contêiner PostgreSQL 18 idêntico ao ambiente local antes de executar qualquer step:

```yaml
services:
  postgres:
    image: postgres:18
    env:
      POSTGRES_USER: datalaw
      POSTGRES_PASSWORD: datalaw
      POSTGRES_DB: datalaw_db
    ports:
      - 5432:5432
```

O contêiner só é considerado pronto quando `pg_isready` responde com sucesso (health-check a cada 10s, 5 tentativas).

### Steps executados em ordem

| # | Step | Comando | Falha se… |
|---|---|---|---|
| 1 | Checkout | `actions/checkout@v4` | repositório inacessível |
| 2 | Configurar Python 3.12 | `actions/setup-python@v5` | versão indisponível |
| 3 | Instalar uv | `astral-sh/setup-uv@v4` | download falhar |
| 4 | Instalar dependências | `uv sync --all-groups` | `uv.lock` inconsistente |
| 5 | **Lint** | `uv run ruff check src tests` | houver erro de estilo/qualidade |
| 6 | **Formatação** | `uv run ruff format --check src tests` | código não estiver formatado |
| 7 | **Testes unitários** | `uv run pytest -m "not integration"` | qualquer teste unitário falhar |
| 8 | **Migrations** | `uv run alembic upgrade head` | migration tiver erro de SQL/schema |
| 9 | **Testes de integração** | `uv run pytest -m "integration"` | qualquer teste de integração falhar |

### Variáveis de ambiente no CI

```
DATABASE_URL=postgresql+psycopg://datalaw:datalaw@localhost:5432/datalaw_db
DATAJUD_API_KEY=${{ secrets.DATAJUD_API_KEY }}
```

### Separação de testes

Os testes do backend são separados por marcador pytest:

```python
# teste unitário — sem banco
def test_main_runs_incremental_ingestion_by_default(fake_cli): ...

# teste de integração — requer banco real
@pytest.mark.integration
def test_bronze_persiste_processos(): ...
```

O `pyproject.toml` registra o marcador e define os diretórios:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["integration: requires a configured PostgreSQL database"]
```

---

## JOB 2 — Build e Deploy do Frontend

**Gatilho:** somente `push` direto para `main`, após o JOB 1 passar  
**Dependência:** `needs: test`

### Steps executados em ordem

| # | Step | Detalhe |
|---|---|---|
| 1 | Checkout | Clona o repositório no runner |
| 2 | Configurar JDK 21 | Temurin, com cache Maven automático |
| 3 | **Testes Java** | `./mvnw test` — falha o job se qualquer teste JUnit falhar |
| 4 | **Build Maven** | `./mvnw package -DskipTests` — gera o JAR (testes já foram rodados) |
| 5 | Renomear JAR | `find target/ … -exec cp {} target/datalaw.jar` |
| 6 | Backup na VM | Renomeia o JAR anterior com timestamp antes de substituir |
| 7 | SCP do JAR | Copia `datalaw.jar` para `/home/azureuser/frontend/` via `scp-action` |
| 8 | Restart do serviço | `systemctl restart datalaw.service` — cria o serviço se não existir |

### Serviço systemd do Frontend

```ini
[Unit]
Description=DataLaw Java Application
After=network.target

[Service]
User=azureuser
ExecStart=/usr/bin/java -jar /home/azureuser/frontend/datalaw.jar
SuccessExitStatus=143
Restart=on-failure
Environment="SERVER_PORT=8080"

[Install]
WantedBy=multi-user.target
```

### Estratégia de backup

Antes de cada deploy, o JAR anterior é preservado com timestamp:

```
datalaw_backup_20261023141500.jar   ← versão anterior
datalaw.jar                         ← versão nova
```

---

## JOB 3 — Deploy do Backend

**Gatilho:** somente `push` direto para `main`, após o JOB 1 passar  
**Dependência:** `needs: test`

### Steps executados em ordem

| # | Step | Detalhe |
|---|---|---|
| 1 | Checkout | Clona o repositório no runner |
| 2 | SCP do backend | Copia toda a pasta `backend/` para `/home/azureuser/backend/` |
| 3 | `uv sync` | Sincroniza as dependências na VM de produção |
| 4 | **Migrations** | `uv run alembic upgrade head` — aplica as migrations pendentes no banco de produção |
| 5 | Restart do serviço | `systemctl restart datalaw-backend.service` — cria o serviço se não existir |

### Serviço systemd do Backend

```ini
[Unit]
Description=DataLaw Python Backend
After=network.target

[Service]
User=azureuser
WorkingDirectory=/home/azureuser/backend
ExecStart=/home/azureuser/backend/start.sh
Restart=on-failure
Environment="LOG_LEVEL=INFO"

[Install]
WantedBy=multi-user.target
```

### Script de inicialização (`start.sh`)

```bash
#!/bin/bash
set -e
echo "⏳ Sincronizando dependências do projeto..."
uv sync
echo "🚀 Iniciando a aplicação..."
uv run python src/data_law/main.py
```

---

## Ambiente Local de Desenvolvimento

Para desenvolvimento local, o banco de dados é provisionado via Docker Compose:

```bash
docker compose up -d
```

**Arquivo:** [`docker-compose.yaml`](file:///media/jackson/DEV/DEV/ProjetoAPI/DataLaw/docker-compose.yaml)

```yaml
services:
  db:
    image: postgres:18
    container_name: datalaw_db
    environment:
      POSTGRES_USER: datalaw
      POSTGRES_PASSWORD: datalaw
      POSTGRES_DB: datalaw_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql
```

### Configuração do `.env`

```
DATAJUD_API_KEY="..."
DATABASE_URL=postgresql+psycopg://datalaw:SUA_SENHA@localhost:5432/datalaw_db
```

### Tarefas disponíveis (`taskipy`)

```bash
uv run task lint          # ruff check
uv run task format        # ruff format --check
uv run task test          # pytest (todos os testes)
uv run task typecheck     # mypy src
uv run task bronze-load   # ingestão camada bronze
uv run task silver-load   # transformação camada silver
uv run task gold-load     # transformação camada gold
uv run task full-ingest   # pipeline completo
```

### Aplicar migrations localmente

```bash
cd backend
uv run alembic upgrade head    # aplica migrations pendentes
uv run alembic downgrade -1    # reverte a última migration
uv run alembic revision --autogenerate -m "descrição"  # gera nova migration
```

---

## Provisionamento da VM (Primeira Vez)

Para configurar uma VM Azure do zero, execute o script [`setup_vm.sh`](file:///media/jackson/DEV/DEV/ProjetoAPI/DataLaw/backend/infra/setup_vm.sh):

```bash
chmod +x backend/infra/setup_vm.sh
./backend/infra/setup_vm.sh
```

O script instala:
- `git`, `curl`, `build-essential` e utilitários base
- **Docker** + Docker Compose (via repositório oficial)
- **uv** (gerenciador de pacotes Python)

> ⚠️ Após a instalação do Docker, é necessário fazer logout e login novamente para que o grupo `docker` tenha efeito.

---

## Secrets do GitHub Actions

Configure os seguintes secrets em **Settings → Secrets and variables → Actions** do repositório:

| Secret | Descrição |
|---|---|
| `AZURE_VM_HOST` | IP ou hostname da VM do backend |
| `AZURE_VM_USER` | Usuário SSH da VM do backend (`azureuser`) |
| `AZURE_VM_SSH_KEY` | Chave SSH privada da VM do backend |
| `AZURE_FRONTEND_VM_HOST` | IP ou hostname da VM do frontend |
| `AZURE_FRONTEND_VM_USER` | Usuário SSH da VM do frontend (`azureuser`) |
| `AZURE_FRONTEND_VM_SSH_KEY` | Chave SSH privada da VM do frontend |
| `DATAJUD_API_KEY` | Chave de acesso à API DataJud |

---

## Comportamento por Tipo de Evento

| Evento | JOB `test` | JOB `frontend` | JOB `backend` |
|---|---|---|---|
| `pull_request` para `main` | ✅ Executa | ❌ Não executa | ❌ Não executa |
| `push` para `main` (testes passam) | ✅ Executa | ✅ Executa | ✅ Executa |
| `push` para `main` (testes falham) | ❌ Falha | ❌ Bloqueado | ❌ Bloqueado |
| `push` para outra branch | ❌ Não dispara | ❌ Não dispara | ❌ Não dispara |

---

## Referências

- [`.github/workflows/deploy.yml`](file:///media/jackson/DEV/DEV/ProjetoAPI/DataLaw/.github/workflows/deploy.yml) — Pipeline CI/CD completo
- [`backend/infra/setup_vm.sh`](file:///media/jackson/DEV/DEV/ProjetoAPI/DataLaw/backend/infra/setup_vm.sh) — Provisionamento da VM
- [`docker-compose.yaml`](file:///media/jackson/DEV/DEV/ProjetoAPI/DataLaw/docker-compose.yaml) — Banco local
- [`backend/start.sh`](file:///media/jackson/DEV/DEV/ProjetoAPI/DataLaw/backend/start.sh) — Inicialização do backend
- [`backend/pyproject.toml`](file:///media/jackson/DEV/DEV/ProjetoAPI/DataLaw/backend/pyproject.toml) — Dependências e tarefas
- [`backend/migration/env.py`](file:///media/jackson/DEV/DEV/ProjetoAPI/DataLaw/backend/migration/env.py) — Configuração do Alembic
