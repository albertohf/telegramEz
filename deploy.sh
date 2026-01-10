#!/bin/bash

echo "🚀 Iniciando Deploy do Telegram API..."

# 1. Garantir que a rede eznet existe
if [ ! "$(docker network ls | grep eznet)" ]; then
  echo "🌐 Criando rede eznet..."
  docker network create eznet
else
  echo "✅ Rede eznet já existe."
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
