#!/bin/bash
# Encerra o script caso algum comando falhe
set -e


echo "⏳ Sincronizando dependências do projeto..."
uv sync

echo "🚀 Iniciando a aplicação..."
uv run python src/data_law/main.py
