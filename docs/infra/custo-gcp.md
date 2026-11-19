# ☁️ Orçamento Estimado — Google Cloud Platform (GCP)
### DataLaw · Backend Python + Frontend Java + PostgreSQL Gerenciado
> Região: **southamerica-east1 (São Paulo)** · Moeda: **USD/mês** · Referência: nov/2026
> Preços no modelo **On-Demand**. Com VMs com Committed Use (1 ano), o desconto é de aproximadamente **37%**.

---

## 🏗️ Arquitetura Provisionada

```
Internet
    │
    ├─► [VM Frontend] e2-medium · Java Spring Boot :8080
    │       Firewall: allow tcp:80, tcp:443, tcp:8080, tcp:22
    │
    ├─► [VM Backend]  e2-medium · Python FastAPI / ETL
    │       Firewall: allow tcp:8000, tcp:22 (tag: backend)
    │
    └─► [Cloud SQL — PostgreSQL 15]
            db-g1-small · 0.5 vCPU · 1.7 GB RAM · 20 GB SSD
            IP Privado (Private Service Access) — sem IP público
```

---

## 💰 Tabela de Custos

### Configuração Mínima _(dev / acadêmico)_

| Recurso | SKU / Tier | Qtd | Preço Unit. (USD/h) | Total (USD/mês) |
|---|---|---|---|---|
| VM Frontend | e2-micro · 2 vCPU burst · 1 GB | 1 | $0,0084 | **$6,13** |
| VM Backend | e2-small · 2 vCPU burst · 2 GB | 1 | $0,0168 | **$12,26** |
| Boot Disk (Standard HDD) | 50 GB por VM | 2 | $0,048/GB | **$4,80** |
| Cloud SQL | db-f1-micro · 1 vCPU · 0.6 GB | 1 | $0,0290 | **$21,17** |
| Cloud SQL Storage | SSD 20 GB | 1 | $0,187/GB | **$3,74** |
| Static IP (External) | Regional · 1 por VM | 2 | $0,0040 | **$5,84** |
| Egress Internet | ≤ 5 GB/mês (América do Sul) | — | $0,12/GB | **~$0,60** |
| **TOTAL MÍNIMO** | | | | **~$54,54/mês** |

---

### Configuração Recomendada _(small production)_

| Recurso | SKU / Tier | Qtd | Preço Unit. (USD/h) | Total (USD/mês) |
|---|---|---|---|---|
| VM Frontend | e2-medium · 2 vCPU · 4 GB | 1 | $0,0469 | **$34,24** |
| VM Backend | e2-medium · 2 vCPU · 4 GB | 1 | $0,0469 | **$34,24** |
| Boot Disk (Standard SSD pd-ssd) | 50 GB por VM | 2 | $0,187/GB | **$18,70** |
| Cloud SQL | db-g1-small · 0.5 vCPU · 1.7 GB | 1 | $0,0500 | **$36,50** |
| Cloud SQL Storage | SSD 20 GB | 1 | $0,187/GB | **$3,74** |
| Cloud SQL Backup | 7 dias automático | 1 | $0,088/GB | **~$1,80** |
| Static IP (External) | Regional · 1 por VM | 2 | $0,0040 | **$5,84** |
| Egress Internet | ≤ 10 GB/mês (América do Sul) | — | $0,12/GB | **~$1,20** |
| **TOTAL RECOMENDADO** | | | | **~$136,26/mês** |

---

## 📉 Economia com Committed Use Discounts (CUD)

| Período | Desconto VMs | Total Mínimo/mês | Total Recomendado/mês |
|---|---|---|---|
| On-Demand | 0% | $54,54 | $136,26 |
| Committed Use 1 ano | ~37% | ~$43,00 | ~$107,53 |
| Committed Use 3 anos | ~55% | ~$34,00 | ~$84,70 |
| Sustained Use (automático) | ~20–30% | ~$42,00 | ~$104,00 |

> [!NOTE]
> GCP aplica automaticamente **Sustained Use Discounts** quando uma VM roda por mais de 25% do mês — sem necessidade de compromisso prévio.

---

## 🔧 Serviços GCP Utilizados

| Serviço | Propósito |
|---|---|
| **Compute Engine (e2-medium)** | Hospedagem das aplicações Backend (Python) e Frontend (Java) |
| **Cloud SQL for PostgreSQL** | Banco de dados gerenciado, backups, failover automático |
| **VPC (Virtual Private Cloud)** | Rede privada isolando DB das VMs |
| **Cloud Firewall Rules** | Regras de entrada/saída por tag de rede |
| **Static External IP** | IPs fixos para acesso às VMs |
| **Cloud Storage (opcional)** | Armazenamento de backups e artefatos de ETL |
| **Private Service Access** | Conexão privada das VMs ao Cloud SQL sem exposição pública |

---

## 🆓 Free Tier GCP

| Recurso | Gratuito/mês |
|---|---|
| Compute Engine | 1x e2-micro (us-central1, us-east1, us-west1) |
| Cloud Storage | 5 GB |
| Egress Internet | 1 GB/mês (exceto China/Austrália) |
| Cloud SQL | ❌ Não incluso no Free Tier |

> [!TIP]
> Novos clientes GCP recebem **$300 de crédito gratuito** por 90 dias. Ideal para validar a infraestrutura antes do comprometimento financeiro.

---

## 📌 Observações

> [!NOTE]
> O Cloud SQL **não possui IP público** — o acesso é feito exclusivamente via Private Service Access (VPC peering interno), seguindo boas práticas de segurança.

> [!WARNING]
> A região `southamerica-east1` (São Paulo) tem custos **10–20% maiores** que `us-central1`. Para projetos de desenvolvimento, considere usar `us-central1` e migrar para São Paulo em produção.

---

## 🔗 Referências Oficiais

- [Calculadora GCP](https://cloud.google.com/products/calculator)
- [Preços Compute Engine](https://cloud.google.com/compute/all-pricing)
- [Preços Cloud SQL](https://cloud.google.com/sql/pricing)
- [GCP Free Tier](https://cloud.google.com/free)
- [Committed Use Discounts](https://cloud.google.com/compute/docs/instances/signing-up-committed-use-discounts)

---
*Estimativa gerada em nov/2026. Consulte a calculadora oficial para valores atualizados.*
