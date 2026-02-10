# Guia de Uso — TelegramEz SaaS

Este guia explica como configurar e utilizar a sua nova plataforma de automação de Telegram.

---

## 🚀 1. Configuração Inicial

### Passo 1: Dependências e Python 3.9
Certifique-se de estar com o ambiente virtual ativo e as dependências instaladas:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Passo 2: Variáveis de Ambiente
Edite o arquivo `.env` na raiz do projeto e insira suas credenciais do **Supabase**:
```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-service-role
```

### Passo 3: Banco de Dados
Copie o conteúdo do arquivo `schema.sql` e execute-o no **SQL Editor** do seu painel do Supabase. Isso criará as tabelas necessárias: `telegram_accounts`, `flows`, `flow_steps` e `conversations`.

---

## 🛠 2. Iniciando a API

Para rodar o servidor principal (FastAPI):
```bash
python main.py
```
A API estará disponível em `http://localhost:8000`. Você pode acessar a documentação interativa em `http://localhost:8000/docs`.

---

## 📱 3. Como usar via API

Abaixo estão exemplos de como interagir com o sistema usando `curl` ou qualquer cliente HTTP (Postman/Insomnia).

### A. Adicionar uma Conta Telegram
Antes de rodar um bot, você precisa registrar as credenciais da conta.
```json
// POST /accounts/
{
  "api_id": 123456,
  "api_hash": "sua_hash_aqui",
  "phone_number": "+5511999999999",
  "session_name": "minha_sessao_01"
}
```

### B. Iniciar o Worker (Bot) da Conta
Cada conta roda em um processo isolado. Para ligar o bot:
```bash
# POST /workers/{account_id}/start
```
*Dica: O ID da conta você recebe ao criá-la ou listá-las em `GET /accounts/`.*

### C. Criar um Flow de Automação
Os flows definem o que o bot faz automaticamente. Aqui está um exemplo de flow que responde a uma mensagem e aguarda o nome do usuário:

**POST `/flows/`**
```json
{
  "account_id": "uuid-da-conta-aqui",
  "name": "Boas Vindas",
  "trigger_type": "first_message",
  "steps": [
    {
      "order": 1,
      "type": "send_text",
      "payload": { "text": "Olá! Eu sou um bot automático. Como você se chama?" }
    },
    {
      "order": 2,
      "type": "wait_message",
      "payload": { "variable": "nome_usuario" }
    },
    {
      "order": 3,
      "type": "send_text",
      "payload": { "text": "Prazer em te conhecer! Vou te enviar uma foto agora." }
    },
    {
      "order": 4,
      "type": "send_image",
      "payload": { 
        "url": "https://pydantic-docs.helpmanual.io/img/logo-white.png",
        "caption": "Pydantic is cool!" 
      }
    },
    {
      "order": 5,
      "type": "end",
      "payload": {}
    }
  ]
}
```

---

## ⚙️ 4. Tipos de Etapas (Steps)

| Tipo | Payload Exemplo | Descrição |
| :--- | :--- | :--- |
| `send_text` | `{ "text": "Olá!" }` | Envia uma mensagem de texto. |
| `send_image`| `{ "url": "...", "caption": "..." }` | Envia uma foto (comprimida). |
| `send_audio`| `{ "url": "...", "voice_note": true }` | Envia áudio como Mensagem de Voz. |
| `send_file` | `{ "url": "...", "caption": "..." }` | Envia qualquer arquivo sem compressão. |
| `wait_message`| `{ "variable": "idade" }` | Para o flow e aguarda o usuário responder. |
| `wait_time` | `{ "seconds": 5 }` | Aguarda X segundos antes de continuar. |
| `end` | `{}` | Finaliza a conversa e limpa o estado. |

---

## 🧠 5. Como o Sistema Funciona

1. **WorkerManager**: Gerencia subprocessos Python. Quando você dá `start` em uma conta, ele executa `python -m app.workers.runner`.
2. **TelegramWorker**: Dentro do worker, ele usa o **Telethon** para escutar mensagens.
3. **FlowEngine**: Quando chega uma mensagem, o worker pergunta ao FlowEngine: "Este usuário tem uma conversa ativa?". 
   - Se sim: Ele processa o próximo passo do flow.
   - Se não: Ele verifica se a mensagem bate com algum "Trigger" (Palavra-chave ou Primeira Mensagem).
4. **Contexto**: Respostas do usuário em steps `wait_message` são salvas na tabela `conversations` (coluna `context`), permitindo que você use esses dados futuramente.

---

## 🛡️ Anti-Ban e Boas Práticas
- Não inicie muitos workers ao mesmo tempo em IPs suspeitos.
- Use `wait_time` entre mensagens para parecer mais humano.
- Evite enviar links em massa para usuários que não têm seu contato salvo.
