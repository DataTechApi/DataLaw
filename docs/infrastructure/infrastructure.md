# Infrastructure Guide — DataLaw

This guide describes what the repository defines. Open points are listed in the [handover risk register](../handover/README.md#risk-register).

## Overview

```text
GitHub (main) ──► GitHub Actions ──┬──► Frontend VM: Spring Boot JAR, port 8080
                                   └──► Backend VM: Python pipelines (uv)

Public sources (DataJud, BNP) ──► Backend VM ──► PostgreSQL ◄── Frontend VM
```

| Component | Technology | Location |
|---|---|---|
| Web application | Java 21, Spring Boot 4.1.1, Thymeleaf | Azure VM, `/home/azureuser/frontend` |
| Data pipelines | Python 3.12, uv | Azure VM, `/home/azureuser/backend` |
| Database | PostgreSQL 18 locally and in CI | Production location to confirm (risk R2) |
| CI/CD | GitHub Actions | `.github/workflows/deploy.yml` |

## Infrastructure files

| File | Purpose |
|---|---|
| `.github/workflows/deploy.yml` | Tests and deploy |
| `backend/infra/setup_vm.sh` | Installs base packages, Docker and uv on an Ubuntu VM |
| `backend/start.sh` | Syncs dependencies and runs the backend entry point |
| `docker-compose.yaml` | Local PostgreSQL only |

The systemd units `datalaw.service` and `datalaw-backend.service` are created by the workflow on first deploy.

## Local environment

Prerequisites: Git, Docker, uv and JDK 21.

```bash
docker compose up -d
```

```bash
cd backend
uv sync --all-groups
uv run alembic upgrade head
```

Create `backend/.env`:

```env
DATAJUD_API_KEY=cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==
DATABASE_URL=postgresql+psycopg://datalaw:datalaw@localhost:5432/datalaw_db
```

Run the frontend with Spring environment variables, since `application.properties` is not versioned:

```bash
cd frontend
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/datalaw_db SPRING_DATASOURCE_USERNAME=datalaw SPRING_DATASOURCE_PASSWORD=datalaw ./mvnw spring-boot:run
```

The local credentials are for development only.

## CI/CD pipeline

| Event | Backend tests | Frontend deploy | Backend deploy |
|---|---|---|---|
| Pull request to `main` | Runs | No | No |
| Push to `main`, tests pass | Runs | Runs | Runs |
| Push to `main`, tests fail | Fails | Blocked | Blocked |
| Push to another branch | No | No | No |

**`test` job:** starts PostgreSQL 18, then runs lint, format check, unit tests, migrations and integration tests for the backend.

**`build-and-deploy-frontend` job:** runs `./mvnw test`, builds the JAR, renames the previous JAR with a timestamp, copies the new one and restarts `datalaw.service`.

**`deploy-backend` job:** copies `backend/`, runs `uv sync`, runs `alembic upgrade head` on the production database and restarts `datalaw-backend.service`.

The two deploy jobs are independent, so one can succeed while the other fails. Frontend test failures happen only here, after the merge.

## Configuration and secrets

**GitHub Actions secrets**

| Secret | Purpose |
|---|---|
| `AZURE_VM_HOST` | Backend VM host |
| `AZURE_VM_USER` | Backend VM SSH user |
| `AZURE_VM_SSH_KEY` | Backend VM private key |
| `AZURE_FRONTEND_VM_HOST` | Frontend VM host |
| `AZURE_FRONTEND_VM_USER` | Frontend VM SSH user |
| `AZURE_FRONTEND_VM_SSH_KEY` | Frontend VM private key |
| `DATAJUD_API_KEY` | DataJud API key |

**Runtime configuration**

| Setting | Component | Where |
|---|---|---|
| `DATABASE_URL` | Backend | `.env` on the VM |
| `DATAJUD_API_KEY` | Backend | `.env` on the VM |
| `LOG_LEVEL` | Backend | systemd unit |
| Datasource settings | Frontend | Not versioned; the location on the VM must be confirmed (risk R1) |
| `SERVER_PORT` | Frontend | systemd unit |

Rotate all secrets at handover. Never store them in the repository.

## Operations runbook

**Check services**

```bash
sudo systemctl status datalaw.service
sudo systemctl status datalaw-backend.service
```

**Run the pipeline manually** (in `/home/azureuser/backend`)

| Command | Effect |
|---|---|
| `uv run python -m data_law.main` | Incremental ingestion |
| `uv run task full-ingest` | Historical ingestion |
| `uv run task bronze-load` | Reprocess raw files into Bronze |
| `uv run task silver-load` | Update Silver |
| `uv run task gold-load` | Rebuild every Gold table |
| `uv run task gold-load -- --name topic_results` | Rebuild one Gold table |

Run `gold-load` after ingestion. The incremental load requires a completed historical load.

**Roll back the frontend**

```bash
cd /home/azureuser/frontend
ls -1t datalaw_backup_*.jar
cp datalaw_backup_YYYYMMDDHHMMSS.jar datalaw.jar
sudo systemctl restart datalaw.service
```

**Roll back the backend:** revert the commit in a pull request and merge it, which deploys the previous code.

**Roll back a migration**

```bash
uv run alembic downgrade -1
```

Back up the database first. A downgrade can lose data.

**Provision a new VM**

1. Create an Ubuntu VM and allow SSH from GitHub Actions.
2. Run `backend/infra/setup_vm.sh`, then log out and back in.
3. For the frontend VM, install JDK 21. The setup script does not install Java.
4. Create the runtime configuration.
5. Update the GitHub secrets.
6. Deploy through a merge to `main`.
