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

# 2. Build da imagem (Swarm não faz build automático)
echo "📦 Construindo imagem Docker..."
docker build -t telegramapi:latest .

# 3. Deploy do Stack no Swarm
echo "⬆️ Fazendo deploy do Stack no Swarm..."
docker stack deploy -c docker-compose.yml telegramapi

echo "✨ Tudo pronto! O serviço está subindo no Swarm."
echo "ℹ️ Verifique o status com: docker service ls | grep telegramapi"
echo "ℹ️ Verifique os logs com: docker service logs -f telegramapi_telegramapi"

