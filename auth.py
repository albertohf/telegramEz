import asyncio
from telethon import TelegramClient

# Use os mesmos valores do seu main.py
api_id = 30991951
api_hash = '8fb828b0a409ce60b66cc87806e981f7'
session_name = 'ezryos'

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    print("Iniciando cliente Telegram para autenticação...")
    await client.start()
    
    if await client.is_user_authorized():
        print("---------------------------------------")
        print("SUCESSO: Você está autenticado!")
        print(f"O arquivo '{session_name}.session' foi atualizado.")
        print("Agora você já pode rodar o 'python main.py'.")
        print("---------------------------------------")
    else:
        print("Falha na autenticação.")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
