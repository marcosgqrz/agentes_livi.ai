FROM python:3.12-slim

WORKDIR /app

# Dependências do sistema necessárias para cryptography/cffi
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python com versões fixas
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Garante que o diretório de builds estáticos existe
RUN mkdir -p web/static/builds

EXPOSE 8080

CMD ["gunicorn", "web.app:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "1", \
     "--worker-class", "gthread", \
     "--threads", "4", \
     "--timeout", "300"]
