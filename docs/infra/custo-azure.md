# ☁️ Orçamento Estimado — Microsoft Azure
### DataLaw · Backend Python + Frontend Java + PostgreSQL Gerenciado
> Região: **Brazil South (São Paulo)** · Moeda: **USD/mês** · Referência: nov/2026
> Preços no modelo **Pay-As-You-Go** (sem reserva). Com VMs reservadas por 1 ano, o desconto é de aproximadamente **40%**.

---

## 🏗️ Arquitetura Provisionada

```
Internet
    │
    ├─► [VM Frontend] Standard_B2s · Java Spring Boot :8080
    │       NSG: allow 80, 443, 8080, 22
    │
    ├─► [VM Backend]  Standard_B2s · Python FastAPI / ETL
    │       NSG: allow 8000, 22 (interno)
    │
    └─► [Azure Database for PostgreSQL Flexible Server]
            Burstable Standard_B2ms · 20 GB SSD
            Acesso restrito via VNET (sem IP público)
```

---

## 💰 Tabela de Custos

### Configuração Mínima _(dev / acadêmico)_

| Recurso | SKU / Tier | Qtd | Preço Unit. (USD/h) | Total (USD/mês) |
|---|---|---|---|---|
| VM Frontend | Standard_B1ms · 1 vCPU · 2 GB | 1 | $0,0271 | **$19,78** |
| VM Backend | Standard_B1ms · 1 vCPU · 2 GB | 1 | $0,0271 | **$19,78** |
| OS Disk (Standard SSD E6) | 64 GB por VM | 2 | — | **$5,20** |
| PostgreSQL Flexible Server | Burstable B1ms · 1 vCPU · 2 GB | 1 | $0,0298 | **$21,75** |
| Armazenamento PostgreSQL | Standard SSD · 20 GB | 1 | — | **$1,60** |
| IP Público Padrão | Static Standard | 2 | $0,005 | **$7,30** |
| Transferência de dados saída | ≤ 5 GB/mês | — | — | **~$0,50** |
| **TOTAL MÍNIMO** | | | | **~$75,91/mês** |

---

### Configuração Recomendada _(small production)_

| Recurso | SKU / Tier | Qtd | Preço Unit. (USD/h) | Total (USD/mês) |
|---|---|---|---|---|
| VM Frontend | Standard_B2s · 2 vCPU · 4 GB | 1 | $0,1086 | **$79,28** |
| VM Backend | Standard_B2s · 2 vCPU · 4 GB | 1 | $0,1086 | **$79,28** |
| OS Disk (Premium SSD P6) | 64 GB por VM | 2 | — | **$19,20** |
| PostgreSQL Flexible Server | Burstable B2ms · 2 vCPU · 8 GB | 1 | $0,0952 | **$69,50** |
| Armazenamento PostgreSQL | Premium SSD · 32 GB | 1 | — | **$3,96** |
| IP Público Padrão | Static Standard | 2 | $0,005 | **$7,30** |
| Backup PostgreSQL (7 dias) | Incluído | — | — | **$0,00** |
| Transferência de dados saída | ≤ 10 GB/mês | — | — | **~$1,00** |
| **TOTAL RECOMENDADO** | | | | **~$259,52/mês** |

---

## 📉 Economia com Reserva

| Período | Desconto | Total Mínimo/mês | Total Recomendado/mês |
|---|---|---|---|
| Pay-As-You-Go | 0% | $75,91 | $259,52 |
| Reserved 1 ano | ~38% | ~$47,06 | ~$160,90 |
| Reserved 3 anos | ~55% | ~$34,16 | ~$116,78 |

---

## 🔧 Serviços Azure Utilizados

| Serviço | Propósito |
|---|---|
| **Azure Virtual Machines** | Hospedagem das aplicações Backend (Python) e Frontend (Java) |
| **Azure Database for PostgreSQL Flexible Server** | Banco de dados gerenciado, backups automáticos, HA opcional |
| **Azure Virtual Network (VNet)** | Rede privada isolando DB das VMs e da Internet |
| **Network Security Group (NSG)** | Regras de firewall por VM |
| **Azure Public IP** | IPs estáticos para acesso SSH e HTTP às VMs |
| **Azure Managed Disk** | Discos persistentes para as VMs |

---

## 📌 Observações

> [!NOTE]
> O banco de dados **não possui IP público** — o acesso é feito exclusivamente via VNET interna, seguindo boas práticas de segurança.

> [!TIP]
> Azure oferece **$200 de crédito gratuito** nos primeiros 30 dias para novas contas. Para projetos acadêmicos, verifique o programa **Azure for Students** (até $100/ano gratuitos).

> [!WARNING]
> Preços do `brazilsouth` podem ser **15–25% mais caros** que `eastus`. Considere usar `eastus` se a latência para usuários no Brasil for aceitável.

---

## 🔗 Referências Oficiais

- [Calculadora Azure](https://azure.microsoft.com/pt-br/pricing/calculator/)
- [Preços VMs Linux](https://azure.microsoft.com/pt-br/pricing/details/virtual-machines/linux/)
- [Preços PostgreSQL Flexible Server](https://azure.microsoft.com/pt-br/pricing/details/postgresql/flexible-server/)
- [Azure for Students](https://azure.microsoft.com/pt-br/free/students/)

---
*Estimativa gerada em nov/2026. Consulte a calculadora oficial para valores atualizados.*
