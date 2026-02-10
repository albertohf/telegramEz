import asyncio
import logging
import requests
from contextlib import asynccontextmanager

from telethon import TelegramClient, events
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

logging.basicConfig(level=logging.INFO)

# SUBSTITUA com seus valores
api_id = 30991951
api_hash = '8fb828b0a409ce60b66cc87806e981f7'
session_name = 'ezryos'
webhook_url = 'https://webhook.ezhot.com.br/webhook/b80f9336-d2cd-41c0-99c7-05b490b92d68'

client = TelegramClient(session_name, api_id, api_hash)

# Modelo para o endpoint de envio
class SendTextRequest(BaseModel):
    chat_id: int
    text: str

class SendFileRequest(BaseModel):
    chat_id: int
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    caption: Optional[str] = None
    voice_note: bool = False
    video_note: bool = False
    force_document: bool = False

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

# Handler de recebimento com suporte a mídia
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return

    sender = await event.get_sender()
    
    # Monta o nome completo
    first_name = getattr(sender, 'first_name', '')
    last_name = getattr(sender, 'last_name', '')
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    
    # Estrutura básica da mensagem
    msg = {
        "sender_id": event.sender_id,
        "sender_username": getattr(sender, 'username', None),
        "sender_first_name": first_name,
        "sender_last_name": last_name,
        "sender_full_name": full_name,
        "sender_phone": getattr(sender, 'phone', None),
        "chat_id": event.chat_id,
        "text": event.raw_text,
        "date": str(event.message.date),
        "message_id": event.message.id,
        "has_media": bool(event.message.media),
        "media_type": None,
        "media_info": {}
    }
    
    # Verifica se há mídia na mensagem
    if event.message.media:
        # Foto
        if event.photo:
            msg["media_type"] = "photo"
            msg["media_info"] = {
                "file_id": event.message.photo.id,
                "access_hash": event.message.photo.access_hash,
                "file_reference": event.message.photo.file_reference.hex() if event.message.photo.file_reference else None
            }
        
        # Documento (inclui áudio, vídeo, arquivo, etc)
        elif event.document:
            doc = event.message.document
            msg["media_info"] = {
                "file_id": doc.id,
                "access_hash": doc.access_hash,
                "file_reference": doc.file_reference.hex() if doc.file_reference else None,
                "file_name": None,
                "mime_type": doc.mime_type,
                "file_size": doc.size,
                "duration": None
            }
            
            # Processa atributos do documento
            for attr in doc.attributes:
                # Nome do arquivo
                if hasattr(attr, 'file_name'):
                    msg["media_info"]["file_name"] = attr.file_name
                
                # Áudio
                if hasattr(attr, 'duration') and hasattr(attr, 'title'):
                    msg["media_type"] = "audio"
                    msg["media_info"]["duration"] = attr.duration
                    msg["media_info"]["title"] = getattr(attr, 'title', None)
                    msg["media_info"]["performer"] = getattr(attr, 'performer', None)
                
                # Vídeo
                elif hasattr(attr, 'duration') and hasattr(attr, 'w'):
                    msg["media_type"] = "video"
                    msg["media_info"]["duration"] = attr.duration
                    msg["media_info"]["width"] = attr.w
                    msg["media_info"]["height"] = attr.h
            
            # Detecta áudio de voz (voice note)
            if event.voice:
                msg["media_type"] = "voice"
            
            # Detecta vídeo circular (video note)
            elif event.video_note:
                msg["media_type"] = "video_note"
            
            # Se não foi identificado como áudio/vídeo, é um documento genérico
            elif msg["media_type"] is None:
                msg["media_type"] = "document"
        
        # Outros tipos de mídia
        elif event.message.media:
            msg["media_type"] = type(event.message.media).__name__

    try:
        resp = requests.post(webhook_url, json=msg, timeout=10)
        logging.info(f"Posted to webhook, status {resp.status_code}")
        logging.info(f"Message data: {msg}")
    except Exception as e:
        logging.error("Erro ao postar no webhook:", exc_info=e)

# Novo endpoint para enviar mensagens (texto, imagem, áudio)
@app.post("/send-text")
async def send_message(request: SendTextRequest):
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
        logging.error(f"Erro ao enviar texto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-file")
async def send_file_endpoint(request: SendFileRequest):
    try:
        file_to_send = request.file_path or request.file_url

        if not file_to_send:
            raise HTTPException(
                status_code=400,
                detail="É necessário fornecer file_path ou file_url"
            )

        message = await client.send_file(
            entity=request.chat_id,
            file=file_to_send,
            caption=request.caption,
            voice_note=request.voice_note,
            video_note=request.video_note,
            force_document=request.force_document
        )

        return {
            "success": True,
            "message_id": message.id,
            "chat_id": request.chat_id,
            "has_media": True,
            "date": str(message.date)
        }

    except Exception as e:
        logging.error(f"Erro ao enviar arquivo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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