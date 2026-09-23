#!/bin/bash
# Script para configurar a VM na Azure (Assumindo sistema Ubuntu)
# Execute este script dentro da sua VM para instalar todas as dependências

set -e

echo "🔄 Atualizando pacotes do sistema..."
sudo apt-get update && sudo apt-get upgrade -y

echo "📦 Instalando pacotes básicos..."
sudo apt-get install -y ca-certificates curl gnupg git software-properties-common wget build-essential

echo "🐳 Instalando Docker e Docker Compose..."
# Adicionar a chave GPG oficial do Docker
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Configurar o repositório
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "👤 Adicionando usuário atual ao grupo docker (para rodar sem sudo)..."
sudo usermod -aG docker $USER
echo "⚠️  Nota: Você precisará sair (logout) e entrar novamente para que as permissões do Docker tenham efeito."

echo "🐍 Instalando uv (Gerenciador de pacotes Python rápido)..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "✅ Configuração da VM concluída com sucesso!"
echo "Para verificar as instalações, rode:"
echo "docker --version"
echo "docker compose version"
echo "~/.local/bin/uv --version"
