FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Expõe a porta que o FastAPI está usando
EXPOSE 8000

CMD ["python", "main.py"]
