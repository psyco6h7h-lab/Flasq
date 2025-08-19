FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (optional but useful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Streamlit config via env
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "Chat_bot.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

