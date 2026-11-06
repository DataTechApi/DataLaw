# Code Governance — DataLaw

These rules define how code enters `main`. Since a merge to `main` deploys to production, they also protect production.

Rules marked **Recommended** are not enforced by files in the repository. The client's team should adopt them in GitHub settings at handover.

## Branching

| Branch | Purpose |
|---|---|
| `main` | Production. Every push triggers a deploy |
| `sprintN` | Integration branch used so far, one per sprint |
| `feature/SCRUM-n-short-name` | **Recommended** for the client's team, for short-lived work |

Workflow:
1. Create a branch from `main`.
2. Commit small changes linked to a task.
3. Open a pull request to `main`.
4. Wait for checks and approval.
5. Merge. The deploy starts automatically.

Never push directly to `main`.

## Commits

Format, in lowercase except for the task ID:

```text
SCRUM-n :emoji: type(scope): short description
```

| Type | Use |
|---|---|
| `feat` | New functionality |
| `fix` | Bug fix |
| `hotfix` | Urgent production fix |
| `refactor` | Code change without behavior change |
| `perf` | Performance improvement |
| `test` | Tests |
| `docs` | Documentation |
| `style` | Formatting only |
| `chore` | Maintenance |
| `build` | Build or external dependencies |
| `ci` | CI/CD |
| `revert` | Reverting a commit |

The README lists the emoji for each type.

## Pull requests

Every pull request must:

- name the task and the requirement it implements;
- describe the change and how it was tested;
- include tests for changed behavior;
- include a migration for schema changes;

**Recommended branch protection for `main`:**

- require a pull request and at least one approval;
- require the `Testes Automatizados (CI)` check;
- require a frontend test check, after adding it (risk R4 in the [handover guide](../handover/README.md));
- block force pushes and branch deletion.

## Review checklist

- Does the change meet the acceptance criteria?
- Are success and failure cases tested?
- Does the code stay within its layer?
- Are SQL inputs bound as parameters?
- Does any screen or indicator expose confidential or personal data?
- Could the migration lose data or lock a large table?
- Is the change safe for production, given that the merge deploys it?

## Quality gates

| Check | Command | Runs in CI on PRs |
|---|---|---|
| Lint | `uv run ruff check src tests` | Yes |
| Format | `uv run ruff format --check src tests` | Yes |
| Backend unit tests | `uv run pytest -m "not integration"` | Yes |
| Migrations | `uv run alembic upgrade head` | Yes |
| Backend integration tests | `uv run pytest -m "integration"` | Yes |
| Type check | `uv run mypy src` | No, run manually |
| Frontend tests | `./mvnw test` | No, only on the deploy job |

## Definition of Done

An item is done when:

- the code is reviewed and merged;
- automated tests pass;
- the acceptance criteria are met;
- the indicator matches the client's reference number, when applicable;
- the Product Owner approves it.

## Data rules

- Never commit `.env`, `application.properties`, keys or production data.
- Do not expose names of parties, CPF, RG or addresses.
- Never run tests with the production `DATABASE_URL`. The integration test writes to and deletes from the database.

## Dependencies

- Python dependencies are locked in `backend/uv.lock`. Change them with `uv add` or `uv remove`, and commit the lock file.
- Java dependencies are defined in `frontend/pom.xml`.
- Review dependency updates in pull requests like any other change.

## Ownership

| Area | Path | Owner |
|---|---|---|
| Pipelines | `backend/` | To be defined by the client |
| Web application | `frontend/` | To be defined by the client |
| CI/CD and infrastructure | `.github/`, `backend/infra/`, `docker-compose.yaml` | To be defined by the client |
| Requirements | `docs/requirements/` | To be defined by the client |
