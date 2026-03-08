# AI Email Response Agent

A small FastAPI service that generates a reply to an input email using OpenAI.

---

## 🏃 Running locally (recommended)

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Set your OpenAI key

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

#### Optional environment variables

You can tweak runtime behavior with the following vars:

- `APP_ENV` (default: `development`)
- `CORS_ORIGINS` (comma-separated list of allowed origins; default: `http://localhost:3000,http://127.0.0.1:3000`)
- `ALLOW_ALL_ORIGINS` (set to `true` to allow all origins; useful for quick public demos)


### 3) Start the server

```bash
uvicorn backend.main:app --reload
```

### 4) Open the UI

- Visit: **http://127.0.0.1:8000/**
- Or use the interactive API docs: **http://127.0.0.1:8000/docs**

### 5) Example request (optional)

```bash
python scripts/demo_request.py
```

---

## 🐳 Run with Docker (portable)

```bash
docker build -t ai-email-agent .

docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  ai-email-agent
```

You can also use `docker-compose`:

```bash
docker compose up --build
```

---

## 🌍 Share it (temporary public URL)

If you want a quick public URL (best for demos), use a tunneling tool:

```bash
# ngrok
ngrok http 8000

# cloudflared
cloudflared tunnel --url http://localhost:8000
```

Then send the generated public URL to your reviewer.

---

## 🚀 Deploy to Render (example)

This repo includes `render.yaml` configured for a simple Python web service.

1) Push to GitHub
2) Connect the repo in Render
3) Add the `OPENAI_API_KEY` environment variable in Render
4) Deploy

Your deployed app will expose the same UI and API at a public URL.

### Render status badge (optional)

Once your service is created, you can optionally add a status badge by replacing `<SERVICE_ID>` with your Render service ID:

```markdown
![Render status](https://api.render.com/v1/services/<SERVICE_ID>/deploys/latest/status)
```

---

## ✅ CI (GitHub Actions)

A CI workflow is included at `.github/workflows/ci.yml`.
It runs on push/pull requests to `main`, and performs:

- dependency install
- syntax validation (`python -m py_compile`)
- tests (`pytest`)

The tests are skipped when `OPENAI_API_KEY` is not set, so CI can run safely without secrets.

---

## 🔁 Auto-deploy to Render (GitHub Actions)

A workflow at `.github/workflows/deploy-render.yml` triggers a Render deploy whenever `main` is updated.

To enable it:

1) Create a Render service for this repo
2) Add these secrets to your GitHub repo:
   - **RENDER_API_KEY** (create from https://dashboard.render.com/api-keys)
   - **RENDER_SERVICE_ID** (found in the service settings URL or API)

If the secrets aren’t set, the workflow will safely skip the deploy step.

---

## 📌 Notes

- Incoming emails are saved into `database/emails.db`.
- Training email data (for similarity search) lives in the `training_emails` table; see `backend/load_training.py`.
- The API endpoint is `POST /generate` with payload:

```json
{ "email": "<your email text>" }
```

### Why the API might return an error
If `OPENAI_API_KEY` is not set, or if the OpenAI request fails, the API now returns an error response (HTTP 500) with a message describing what went wrong.

To fix this, ensure `OPENAI_API_KEY` is set in your environment before starting the server.

### Running with a local model (no OpenAI quota needed)
If you want to run the app without an OpenAI API key (e.g., to avoid quota/billing), you can use a local model.

1) Install a local model backend (choose one):
   - `pip install gpt4all` (recommended)
   - or `pip install llama-cpp-python`

2) Download a model file (or use a built-in gpt4all model):
   - For `gpt4all`, you can use a built-in model name like `ggml-gpt4all-j-v1.3-groovy`.
   - For `llama-cpp-python`, download a `.bin`/`.ggml` model and set `LOCAL_MODEL_PATH`.

3) Start the server using local model mode:

```bash
export LOCAL_LLM=1
# Optional: specify which model to use:
export LOCAL_MODEL_NAME="ggml-gpt4all-j-v1.3-groovy"
# or
# export LOCAL_MODEL_PATH="/path/to/your/model.ggml"

uvicorn backend.main:app --reload
```

If local model generation fails, the app will return an error explaining which local backend is missing or what went wrong.

> If you see an error about `HTTP 404 Not Found`, it usually means the default `gpt4all` model name is no longer available for download. In that case:
>
> 1) Download a local model manually (e.g., from https://gpt4all.io or https://github.com/nomic-ai/gpt4all/releases).
> 2) Set `LOCAL_MODEL_PATH` to the downloaded `.ggml` file.
>
> Example:
>
> ```bash
> export LOCAL_MODEL_PATH="/path/to/ggml-gpt4all-j-v1.3-groovy.ggml"
> export LOCAL_LLM=1
> uvicorn backend.main:app --reload
> ```

### Health check

The service exposes a simple health endpoint:

```
GET /healthz
```

It responds with:

```json
{ "status": "ok" }
```
