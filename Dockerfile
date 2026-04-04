FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Ensure static build dir exists
RUN mkdir -p web/static/builds

EXPOSE 8080

CMD ["gunicorn", "web.app:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--worker-class", "gthread", \
     "--threads", "4", \
     "--timeout", "300"]
