# frontend/Dockerfile (Painel Admin)
FROM python:3.11-slim

WORKDIR /app

# Instala dependências básicas do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala requisitos específicos do frontend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do frontend
COPY . .

# Expõe a porta do Flask
EXPOSE 5700

# Inicia com Gunicorn (servidor de produção)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5700", "--workers", "3"]