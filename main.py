import asyncio
import logging
import requests
from contextlib import asynccontextmanager

from telethon import TelegramClient, events
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)

# SUBSTITUA com seus valores
api_id = 37950946
api_hash = 'acbfa58fccc0c2b66980db6edd84722d'
session_name = 'meusession'
webhook_url = 'https://automation.ezhot.com.br/webhook-test/b80f9336-d2cd-41c0-99c7-05b490b92d68'

client = TelegramClient(session_name, api_id, api_hash)

# Modelo para o endpoint de envio
class SendMessageRequest(BaseModel):
    chat_id: int
    text: str

# Gerenciamento do ciclo de vida do cliente Telegram
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inicia o cliente Telegram
    await client.start()
    logging.info("Cliente Telegram iniciado")
    
    # Inicia o handler de mensagens em background
    asyncio.create_task(client.run_until_disconnected())
    
    yield
    
    # Shutdown: desconecta o cliente
    await client.disconnect()
    logging.info("Cliente Telegram desconectado")

app = FastAPI(lifespan=lifespan)

# Handler de recebimento (mantido igual)
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return

    sender = await event.get_sender()
    
    msg = {
        "sender_id": event.sender_id,
        "sender_username": getattr(sender, 'username', None),
        "chat_id": event.chat_id,
        "text": event.raw_text,
        "date": str(event.message.date)
    }

    try:
        resp = requests.post(webhook_url, json=msg, timeout=10)
        logging.info(f"Posted to webhook, status {resp.status_code}")
    except Exception as e:
        logging.error("Erro ao postar no webhook:", exc_info=e)

# Novo endpoint para enviar mensagens
@app.post("/send-message")
async def send_message(request: SendMessageRequest):
    """
    Envia uma mensagem para um chat específico via Telegram.
    
    Body JSON:
    {
        "chat_id": 123456789,
        "text": "Sua mensagem aqui"
    }
    """
    try:
        message = await client.send_message(
            entity=request.chat_id,
            message=request.text
        )
        
        return {
            "success": True,
            "message_id": message.id,
            "chat_id": request.chat_id,
            "text": request.text,
            "date": str(message.date)
        }
    
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao enviar mensagem: {str(e)}"
        )

# Endpoint de health check
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "telegram_connected": client.is_connected()
    }

if __name__ == '__main__':
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )