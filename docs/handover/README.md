# Handover Guide — DataLaw

The contractual deliverable is the **source code and the infrastructure structure**. Future development belongs to the client's development team. This guide is their starting point.

## Reading order

| # | Document | Purpose |
|---|---|---|
| 1 | [Project README](../../README.md) | Product, scope and backlog |
| 2 | [Code guide](../code/code-guide.md) | Repository structure, data flow and how to extend the code |
| 3 | [Code governance](../governance/code-governance.md) | Branches, commits, reviews, quality gates and ownership |
| 4 | [Infrastructure guide](../infrastructure/infrastructure.md) | Environments, CI/CD, secrets and operations |
| 5 | [Test strategy](../testing/test-strategy.md) | How the code is verified |
| 6 | [Test cases](../testing/test-cases.md) | Catalogue of automated tests |
| 7 | [Requirements](../requirements/README.md) | Requirements, use cases and traceability |

## Handover checklist

| # | Item | Owner | Done |
|---|---|---|---|
| 1 | Transfer the GitHub repository or grant the client admin rights | DataTech and client | ☐ |
| 2 | Transfer or recreate the Azure resources | DataTech and client | ☐ |
| 3 | Provide the production frontend configuration | DataTech | ☐ |
| 4 | Confirm the production database location and backups | DataTech | ☐ |
| 5 | Define code owners and branch protection | Client | ☐ |
| 6 | Run a supervised deploy with the client's team | Both | ☐ |
