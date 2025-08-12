## Flasq AI Assistant (Streamlit + Ollama)

This is a Streamlit-based chat UI that talks to an [Ollama](https://ollama.ai) server. It reads its configuration from environment variables or Streamlit secrets.

### Features
- Customizable via `.env` or Streamlit `secrets.toml`
- Select from available Ollama models
- Docker and Docker Compose support

---

### 1) Requirements
- Python 3.10+
- An accessible Ollama server (local or remote)

---

### 2) Quick Start (Local)
1. Clone the repo and enter the directory.
2. Create and populate your environment file:
   ```bash
   cp .env.example .env
   # then edit .env as needed
   ```
3. Create a virtual environment and install deps:
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\\Scripts\\Activate.ps1
   # macOS/Linux
   # source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Ensure Ollama is running and has your model:
   ```bash
   ollama serve
   ollama pull llama3.2:1b
   ```
5. Run the app:
   ```bash
   streamlit run Chat_bot.py
   ```

The app will be available at `http://localhost:8501`.

---

### 3) Docker
Build and run with Docker:
```bash
docker build -t flasq-chatbot .
docker run --rm -p 8501:8501 --env-file .env \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  flasq-chatbot
```

Using Docker Compose:
```bash
docker compose up --build
```

Notes:
- On Docker Desktop (Windows/macOS), containers can reach your host Ollama via `http://host.docker.internal:11434`.
- On Linux, run Ollama in another container or expose the host network appropriately.

---

### 4) Deploying

#### Streamlit Community Cloud
1. Push this repo to GitHub.
2. Create a new Streamlit app from your repo and select `Chat_bot.py` as the entry point.
3. In the app’s Settings → Secrets, add entries matching your `.env` keys (e.g. `OLLAMA_BASE_URL`, `DEFAULT_MODEL`, `PAGE_TITLE`, `APP_NAME`).
4. Deploy. The app will use secrets automatically over `.env`.

#### Any Docker-friendly host (Render, Fly.io, etc.)
1. Push to GitHub.
2. Configure a Docker build and set the environment variables from `.env` in your host’s dashboard.
3. Expose port 8501 and start with the command:
   ```bash
   streamlit run Chat_bot.py --server.port $PORT --server.address 0.0.0.0
   ```

---

### 5) Configuration
Environment variables (via `.env` or host/CI):
- `OLLAMA_BASE_URL`: Base URL to your Ollama server (e.g., `http://localhost:11434`).
- `DEFAULT_MODEL`: Default model name (e.g., `llama3.2:1b`).
- `PAGE_TITLE`: Title shown in the browser tab.
- `APP_NAME`: Branding text shown in the app header.

Streamlit secrets (Cloud): create `.streamlit/secrets.toml` with:
```toml
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL   = "llama3.2:1b"
PAGE_TITLE      = "THIS IS YOUR FLASQ AI ASSISTANT"
APP_NAME        = "Flasq"
```

---

### 6) Pushing to GitHub
```bash
git init
git add .
git commit -m "Initial commit: Flasq AI Assistant"
git branch -M main
git remote add origin <your_repo_url>
git push -u origin main
```

`.env` and `secrets.toml` are ignored by git. Use `.env.example` and this README to document needed values.

---

### 7) License
Use your preferred license (MIT recommended) and include a `LICENSE` file.

