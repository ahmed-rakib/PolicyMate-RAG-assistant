# Build the frontend stylesheet
FROM node:24-bookworm-slim AS frontend

WORKDIR /frontend

RUN npm install --no-audit --no-fund \
    tailwindcss@4.3.3 \
    @tailwindcss/cli@4.3.3

COPY app/static/index.html ./index.html
COPY app/static/input.css ./input.css
COPY app/static/script.js ./script.js

RUN node --check script.js \
    && npx @tailwindcss/cli \
    -i ./input.css \
    -o ./style.css \
    --minify


# Run the Python application
FROM python:3.14.7-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/appuser/.cache/huggingface

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt ./requirements.txt

RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip check

COPY --chown=appuser:appuser app ./app

# Replace any old stylesheet with the newly compiled CSS
COPY --from=frontend --chown=appuser:appuser \
    /frontend/style.css /app/app/static/style.css

RUN mkdir -p /app/data/vector_store \
    /home/appuser/.cache/huggingface \
    && chown -R appuser:appuser \
    /app/data \
    /home/appuser/.cache

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]