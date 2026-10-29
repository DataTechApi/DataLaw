# Arquitetura e Processos do Sistema DataLaw

Este documento descreve a arquitetura tecnológica e os processos estabelecidos no projeto DataLaw. O sistema é desenhado para capturar, processar e exibir grandes volumes de dados de processos judiciais de forma desacoplada e performática.

---

## 1. Visão Geral da Arquitetura

A arquitetura do sistema segue um modelo de **microsserviços lógicos** divididos pela sua finalidade de negócio, onde a ingestão/tratamento de dados é separada da exibição dos dados para o usuário final. 

O sistema é dividido em três pilares fundamentais:
1. **Backend de Engenharia de Dados (Python)**
2. **Frontend e Aplicação Web (Java / Spring Boot)**
3. **Persistência de Dados (Azure PostgreSQL)**

---

## 2. Tecnologias e Componentes

### 2.1 Backend (Python - Ingestão e Processamento)
O backend é totalmente focado no conceito de *pipelines de dados*, utilizando a **Arquitetura Medalhão (Medallion Architecture)**:
* **Bronze:** Dados brutos ingeridos a partir de fontes como o DataJud.
* **Silver:** Dados limpos, padronizados e tipados.
* **Gold:** Dados agregados e modelados para gerar insights e métricas diretas (ex: contagem de processos, taxas de sucesso).

**Stack Tecnológico:**
* **Python 3.12** com gerenciamento rigoroso de pacotes através do **`uv`**.
* Motores de processamento de dados modernos e ultra-rápidos: **DuckDB**, **Polars** e **Pandas**.
* **SQLAlchemy** e **Alembic** para o mapeamento objeto-relacional (ORM) e migrações de banco.
* Scripts automatizados para gerenciar as cargas (`bronze-load`, `silver-load`, `gold-load`).

### 2.2 Frontend (Java - Web MVC e Apresentação)
A aplicação responsável por servir os dados tratados para os usuários finais é construída em Java 21 utilizando o ecossistema Spring Boot.

**Stack Tecnológico:**
* **Java 21** e **Maven**.
* **Spring Boot 4.1.1** (Web MVC) para gerenciamento das requisições web (Controllers).
* **Spring Data JPA** (com Hibernate) para comunicação com o banco de dados.
* **Thymeleaf** para a camada de visualização (Server-Side Rendering), mesclando HTML com os dados de forma dinâmica e leve.
* **Lombok** para redução de código repetitivo e **HikariCP** para gerenciar o pool de conexões.

### 2.3 Banco de Dados (Azure)
* **PostgreSQL:** Hospedado em nuvem de forma gerenciada na Microsoft Azure (`datalawserver.postgres.database.azure.com`).
* Contém múltiplos esquemas (schemas) para separar os dados das diferentes camadas (Silver, Gold, etc.).

---

## 3. Infraestrutura e CI/CD (DevOps)

As aplicações rodam em Máquinas Virtuais (VMs) na nuvem, totalmente desacopladas. O processo de **Integração e Entrega Contínua (CI/CD)** é gerenciado pelo **GitHub Actions** (`deploy.yml`).

O pipeline realiza o deploy em duas etapas distintas assim que o código é mergeado na branch `main`:
1. **Deploy Frontend:**
   - Realiza o build do `.jar` usando o Maven (`./mvnw clean package`).
   - Copia o binário final para a **VM do Frontend**.
   - Cria/Atualiza um serviço nativo no Linux (via `systemd`) e reinicia a aplicação Spring Boot na porta 8080.
2. **Deploy Backend:**
   - Sincroniza o diretório Python inteiro com a **VM do Backend**.
   - Instala/Atualiza as dependências do Python rodando `uv sync`.
   - Gerencia a execução dos scripts ou servidores através de seu próprio serviço no `systemd` (`datalaw-backend.service`).

---

## 4. O Processo (Fluxo de Dados e Desenvolvimento)

Com base no layout, os processos do negócio e da equipe parecem operar da seguinte maneira:

1. **Extração Diária (Ingestão):** O Backend (Python) entra em cena periodicamente (agendado via Cron ou pelo próprio serviço Systemd) consultando fontes governamentais e tribunais (DataJud). 
2. **Refinamento:** Esse dado cru passa por limpezas e filtros até atingir a camada `gold` (dados de negócio consolidados).
3. **Consumo:** Os usuários acessam a aplicação Java através do navegador (Thymeleaf). Os repositórios do Spring consultam diretamente o PostgreSQL nas camadas `silver` ou `gold`, garantindo buscas flexíveis via SQL nativo (usando filtros textuais como `ILIKE`).
4. **Implantação Rápida:** Graças ao GitHub Actions, qualquer correção em consultas (como acabamos de fazer) pode ser enviada com um `git push` e, em questão de minutos, reflete em produção na nuvem, sem intervenção humana.
