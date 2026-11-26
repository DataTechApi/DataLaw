# ☁️ Orçamento Estimado — Amazon Web Services (AWS)
### DataLaw · Backend Python + Frontend Java + PostgreSQL Gerenciado
> Região: **sa-east-1 (São Paulo)** · Moeda: **USD/mês** · Referência: nov/2026
> Preços no modelo **On-Demand**. Com Reserved Instances (1 ano, No Upfront), o desconto é de aproximadamente **38%**.

---

## 🏗️ Arquitetura Provisionada

```
Internet
    │  (Internet Gateway)
    │
    ├─► [EC2 Frontend] t3.medium · Java Spring Boot :8080
    │       SG: allow 80, 443, 8080, 22
    │       Subnet Pública AZ-a
    │
    ├─► [EC2 Backend]  t3.medium · Python FastAPI / ETL
    │       SG: allow 8000, 22 (interno)
    │       Subnet Pública AZ-b
    │
    └─► [RDS PostgreSQL 17 — Multi-AZ opcional]
            db.t3.small · 2 vCPU · 2 GB · 20 GB gp3
            Subnet Privada (DB Subnet Group) — sem IP público
```

---

## 💰 Tabela de Custos

### Configuração Mínima _(dev / acadêmico)_

| Recurso | SKU / Tier | Qtd | Preço Unit. (USD/h) | Total (USD/mês) |
|---|---|---|---|---|
| EC2 Frontend | t3.small · 2 vCPU · 2 GB | 1 | $0,0288 | **$21,02** |
| EC2 Backend | t3.small · 2 vCPU · 2 GB | 1 | $0,0288 | **$21,02** |
| EBS Volume (gp3) | 30 GB por instância | 2 | $0,16/GB | **$9,60** |
| RDS PostgreSQL | db.t3.micro · 2 vCPU · 1 GB | 1 | $0,0280 | **$20,44** |
| RDS Storage (gp3) | 20 GB | 1 | $0,138/GB | **$2,76** |
| Elastic IP | 1 por instância EC2 | 2 | $0,005 | **$7,30** |
| Data Transfer Out | ≤ 5 GB/mês | — | $0,25/GB | **~$1,25** |
| **TOTAL MÍNIMO** | | | | **~$83,39/mês** |

---

### Configuração Recomendada _(small production)_

| Recurso | SKU / Tier | Qtd | Preço Unit. (USD/h) | Total (USD/mês) |
|---|---|---|---|---|
| EC2 Frontend | t3.medium · 2 vCPU · 4 GB | 1 | $0,0576 | **$42,05** |
| EC2 Backend | t3.medium · 2 vCPU · 4 GB | 1 | $0,0576 | **$42,05** |
| EBS Volume (gp3) | 30 GB por instância | 2 | $0,16/GB | **$9,60** |
| RDS PostgreSQL | db.t3.small · 2 vCPU · 2 GB | 1 | $0,0560 | **$40,88** |
| RDS Storage (gp3) | 20 GB | 1 | $0,138/GB | **$2,76** |
| RDS Backup | 7 dias automático | — | Incluído | **$0,00** |
| Elastic IP | 1 por instância EC2 | 2 | $0,005 | **$7,30** |
| Data Transfer Out | ≤ 10 GB/mês | — | $0,25/GB | **~$2,50** |
| **TOTAL RECOMENDADO** | | | | **~$147,14/mês** |

---

## 📉 Economia com Reserved Instances

| Plano | Desconto | Total Mínimo/mês | Total Recomendado/mês |
|---|---|---|---|
| On-Demand | 0% | $83,39 | $147,14 |
| Reserved 1 ano (No Upfront) | ~38% | ~$51,70 | ~$91,23 |
| Reserved 1 ano (All Upfront) | ~43% | ~$47,53 | ~$83,87 |
| Reserved 3 anos (All Upfront) | ~60% | ~$33,36 | ~$58,86 |
| Savings Plans (Compute) | ~até 66% | variável | variável |

---

## 🔧 Serviços AWS Utilizados

| Serviço | Propósito |
|---|---|
| **EC2 (t3.medium)** | Hospedagem das aplicações Backend (Python) e Frontend (Java) |
| **Amazon RDS for PostgreSQL** | Banco de dados gerenciado, backups automáticos, ponto de restauração |
| **VPC** | Rede privada isolando recursos |
| **Security Groups** | Firewall stateful por instância |
| **Elastic IP** | IPs estáticos para as instâncias EC2 |
| **Internet Gateway** | Roteamento da VPC para a Internet |
| **DB Subnet Group** | Subnets privadas para o RDS (sem exposição pública) |
| **IAM Roles** | Permissões de acesso aos serviços AWS (opcional, recomendado) |

---

## 🆓 AWS Free Tier

| Recurso | Gratuito/mês (12 meses) |
|---|---|
| EC2 | 750h t2.micro ou t3.micro |
| RDS | 750h db.t2.micro + 20 GB armazenamento |
| EBS | 30 GB gp2 |
| Data Transfer | 15 GB egress |

> [!TIP]
> Se for uma conta nova na AWS, toda a infraestrutura mínima pode ser coberta pelo **Free Tier** durante os primeiros 12 meses, usando instâncias `t2.micro`/`t3.micro` e `db.t2.micro`.

---

## 📌 Observações

> [!NOTE]
> O RDS **não possui IP público** — o acesso é feito exclusivamente via Security Group interno (ingress na porta 5432 apenas para as instâncias EC2). O DB Subnet Group usa subnets privadas (sem rota para o Internet Gateway).

> [!WARNING]
> A região `sa-east-1` (São Paulo) tem custos **30–50% maiores** que `us-east-1`. Para projetos de desenvolvimento, considere usar `us-east-1` e migrar para São Paulo em produção.

> [!CAUTION]
> **Data Transfer** na AWS tem custo significativo na região `sa-east-1` ($0,25/GB de saída para a Internet). Em cargas de trabalho com muito tráfego de saída (ex.: APIs públicas com resposta grande), o custo pode escalar rapidamente.

---

## 📊 Comparativo Final das Três Nuvens

| Nuvem | Região | Mínimo/mês | Recomendado/mês | Ponto forte |
|---|---|---|---|---|
| **Azure** | brazilsouth | ~$75,91 | ~$259,52 | Integração Microsoft / DevOps |
| **GCP** | southamerica-east1 | ~$54,54 | ~$136,26 | Melhor custo-benefício |
| **AWS** | sa-east-1 | ~$83,39 | ~$147,14 | Maior ecossistema de serviços |

> Para o contexto acadêmico do projeto DataLaw, **GCP** oferece o menor custo e um crédito inicial de $300, sendo uma boa opção para experimentação.

---

## 🔗 Referências Oficiais

- [Calculadora AWS](https://calculator.aws/pricing/2/home)
- [Preços EC2 — sa-east-1](https://aws.amazon.com/ec2/pricing/on-demand/)
- [Preços RDS PostgreSQL](https://aws.amazon.com/rds/postgresql/pricing/)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [AWS Savings Plans](https://aws.amazon.com/savingsplans/)

---
*Estimativa gerada em nov/2026. Consulte a calculadora oficial para valores atualizados.*
