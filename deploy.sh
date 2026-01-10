#!/bin/bash

echo "🚀 Iniciando Deploy do Telegram API..."

# 1. Garantir que a rede eznet existe e é acessível
NETWORK_NAME="eznet"
if [ ! "$(docker network ls | grep $NETWORK_NAME)" ]; then
  echo "🌐 Criando rede $NETWORK_NAME..."
  docker network create $NETWORK_NAME
else
  echo "✅ Rede $NETWORK_NAME já existe."
  # Tenta verificar se é attachable em caso de erro futuro
  echo "ℹ️  Se der erro de 'PermissionDenied' na rede, rode: docker network rm $NETWORK_NAME && docker network create $NETWORK_NAME"
fi

# 2. Build da imagem
echo "📦 Construindo imagem Docker..."
docker build -t telegramapi:latest .

# 3. Subir o container usando docker-compose
echo "⬆️ Subindo container..."
docker compose up -d

echo "✨ Tudo pronto! A API deve estar disponível em: https://telegramapi.ezhot.com.br/health"
echo "📝 Logs do container:"
docker logs --tail 20 telegramapi
