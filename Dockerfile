FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV API_BASE_URL="https://router.huggingface.co/v1"
ENV MODEL_NAME="gpt-4o-mini"
ENV HF_TOKEN=""

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

RUN chmod +x /app/launch.sh

CMD ["/app/launch.sh"]
