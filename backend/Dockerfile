FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# start.sh seeds (idempotent) then runs uvicorn on $PORT. Using a script avoids
# shell-quoting issues with platform "docker command" overrides (e.g. Render).
CMD ["sh", "start.sh"]
