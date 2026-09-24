FROM python:3.12-slim

# Copia o uv da imagem oficial para ter o pacote instalado
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Configura o diretório de trabalho
WORKDIR /app

# Copia os arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instala as dependências de produção sem instalar dependências de desenvolvimento
RUN uv sync --frozen --no-dev

# Copia o restante do código do projeto
COPY . .

# Comando padrão. O main.py no momento é um script de ingestão.
# Se no futuro houver um servidor FastAPI (uvicorn), este comando deverá ser atualizado.
CMD ["uv", "run", "python", "src/data_law/main.py"]
