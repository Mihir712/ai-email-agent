from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .agent import run_agent
from .config import ALLOW_ALL_ORIGINS, APP_ENV, CORS_ORIGINS


class EmailRequest(BaseModel):
    email: str


app = FastAPI(
    title="AI Email Response Agent",
    description="Generate short replies for incoming email text using OpenAI.",
    version="1.0",
)


# Configure CORS for production/preview use cases.
if ALLOW_ALL_ORIGINS:
    allow_origins = ["*"]
else:
    allow_origins = CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    """Serve a small HTML landing page describing the API."""
    return """
    <!DOCTYPE html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
        <title>AI Email Response Agent</title>
        <style>
          :root {
            --bg: #0b1220;
            --card: rgba(255, 255, 255, 0.08);
            --card-border: rgba(255, 255, 255, 0.15);
            --text: #e7eef8;
            --muted: rgba(231, 238, 248, 0.75);
            --accent: #78c0ff;
            --accent-2: #a8ffb3;
            --shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
          }

          * { box-sizing: border-box; }

          .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
          }

          body {
            margin: 0;
            min-height: 100vh;
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--text);
            background: radial-gradient(circle at 20% 10%, rgba(120, 192, 255, 0.35), transparent 55%),
                        radial-gradient(circle at 80% 80%, rgba(168, 255, 179, 0.25), transparent 55%),
                        linear-gradient(135deg, #050914 0%, #0b1220 55%, #07101a 100%);
          }

          .page {
            width: min(980px, 100%);
            margin: 0 auto;
            padding: 3.5rem 1.5rem 2.5rem;
          }

          header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 1rem;
            margin-bottom: 2rem;
          }

          header h1 {
            font-size: clamp(1.8rem, 4vw, 2.4rem);
            margin: 0;
          }

          header p {
            margin: 0;
            color: var(--muted);
          }

          .card {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            box-shadow: var(--shadow);
            padding: 2rem;
          }

          textarea {
            width: 100%;
            min-height: 170px;
            padding: 1rem;
            border-radius: 0.75rem;
            border: 1px solid rgba(255, 255, 255, 0.18);
            background: rgba(255, 255, 255, 0.06);
            color: var(--text);
            resize: vertical;
            font-family: ui-monospace, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            font-size: 0.95rem;
            line-height: 1.5;
          }

          textarea:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(120, 192, 255, 0.25);
          }

          button {
            border: none;
            border-radius: 999px;
            padding: 0.75rem 1.4rem;
            cursor: pointer;
            font-weight: 600;
            font-size: 1rem;
            letter-spacing: 0.01em;
            transition: transform 150ms ease, box-shadow 150ms ease;
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: #0b1220;
          }

          button:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 18px 32px rgba(120, 192, 255, 0.25);
          }

          button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
          }

          .hint {
            font-size: 0.9rem;
            color: var(--muted);
            margin-top: 0.5rem;
          }

          .response {
            margin-top: 1.75rem;
            padding: 1.25rem;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 0.85rem;
          }

          .response h2 {
            margin: 0 0 0.75rem;
            font-size: 1.1rem;
            color: var(--text);
          }

          .response pre {
            white-space: pre-wrap;
            word-break: break-word;
            margin: 0;
            font-family: ui-monospace, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            font-size: 0.95rem;
            line-height: 1.5;
            color: rgba(231, 238, 248, 0.92);
          }

          .footer {
            margin-top: 2.25rem;
            font-size: 0.9rem;
            color: var(--muted);
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            align-items: center;
          }

          .footer a {
            color: rgba(120, 192, 255, 0.9);
            text-decoration: none;
          }

          .footer a:hover {
            text-decoration: underline;
          }

          .pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            background: rgba(255, 255, 255, 0.06);
            font-size: 0.85rem;
          }

          .pill span {
            font-weight: 600;
            color: rgba(231, 238, 248, 0.9);
          }

          .toast {
            position: fixed;
            left: 50%;
            bottom: 1.5rem;
            transform: translateX(-50%);
            background: rgba(23, 34, 53, 0.95);
            color: rgba(231, 238, 248, 0.9);
            border-radius: 0.9rem;
            padding: 0.85rem 1.1rem;
            box-shadow: 0 20px 34px rgba(0, 0, 0, 0.45);
            display: none;
            align-items: center;
            gap: 0.6rem;
            font-size: 0.95rem;
          }

          .toast.show {
            display: flex;
            animation: fadein 250ms ease-out;
          }

          @keyframes fadein {
            from { opacity: 0; transform: translate(-50%, 10px); }
            to { opacity: 1; transform: translate(-50%, 0); }
          }

          @media (max-width: 640px) {
            .page { padding: 2.5rem 1rem; }
            button { width: 100%; }
          }
        </style>
      </head>
      <body>
        <div class=\"page\">
          <header>
            <div>
              <h1>AI Email Response Agent</h1>
              <p>Paste an email below, then click <strong>Generate</strong> to see a model response instantly.</p>
            </div>
            <div class=\"pill\">
              <span>API</span>
              <span>/generate</span>
            </div>
          </header>

          <section class=\"card\">
            <form id=\"generateForm\">              <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem;">
                <label for="templateSelect" style="font-weight: 600; color: var(--muted);">Quick templates</label>
                <select id="templateSelect" style="flex: 1; min-width: 220px; padding: 0.65rem 0.75rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.06); color: var(--text);">
                  <option value="">— pick a template —</option>
                  <option value="meeting">Schedule a meeting</option>
                  <option value="followup">Follow up / reminder</option>
                  <option value="thankyou">Thank you + next steps</option>
                </select>
                <button type="button" id="loadTemplateBtn" style="background: rgba(255,255,255,0.12); color: rgba(231,238,248,0.9);">Load</button>
              </div>
              <label for=\"emailInput\" class=\"sr-only\">Email content</label>
              <textarea id=\"emailInput\" placeholder=\"Write or paste the email content here...\" spellcheck=\"true\" autofocus></textarea>
              <div class=\"hint\">You can paste entire email threads; the model will respond based on the full context.</div>
              <div style=\"margin-top: 1.25rem; display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center;\">
                <button type=\"submit\" id=\"generateBtn\">Generate response</button>
                <button type=\"button\" id=\"clearBtn\" style=\"background: rgba(255,255,255,0.09); color: rgba(231,238,248,0.9);\">Clear</button>
                <span class=\"pill\"><span>Docs</span><a href=\"/docs\" style=\"color: rgba(120,192,255,0.9); margin-left: 0.35rem;\">/docs</a></span>
              </div>
            </form>

            <div id=\"response\" class=\"response\" hidden>
              <div style=\"display: flex; justify-content: space-between; align-items: center; gap: 0.75rem;\">
                <h2>Response</h2>
                  <div id="responseMeta" style="color: rgba(231, 238, 248, 0.75); font-size: 0.9rem;">&nbsp;</div>
                <button id=\"copyBtn\" style=\"background: rgba(255,255,255,0.12); color: rgba(231,238,248,0.9); border-radius: 999px; padding: 0.45rem 0.75rem; border: none; cursor: pointer; font-size: 0.9rem;\">Copy</button>
              </div>
              <pre id=\"responseText\"></pre>
            </div>
          </section>

          <footer class=\"footer\">
            <div>Run the demo: <code>python scripts/demo_request.py</code></div>
            <div>Requires <code>OPENAI_API_KEY</code> &amp; the server running via <code>uvicorn backend.main:app --reload</code></div>
            <div><a class=\"pill\" href=\"https://dashboard.render.com/new\" target=\"_blank\" rel=\"noreferrer\">Deploy to Render</a></div>
          </footer>
        </div>

        <div id=\"toast\" class=\"toast\"></div>

        <script>
          const form = document.getElementById('generateForm');
          const emailInput = document.getElementById('emailInput');
          const responseContainer = document.getElementById('response');
          const responseText = document.getElementById('responseText');
          const responseMeta = document.getElementById('responseMeta');
          const generateBtn = document.getElementById('generateBtn');
          const clearBtn = document.getElementById('clearBtn');
          const copyBtn = document.getElementById('copyBtn');
          const templateSelect = document.getElementById('templateSelect');
          const loadTemplateBtn = document.getElementById('loadTemplateBtn');
          const toast = document.getElementById('toast');

          const templates = {
            meeting: `Hi [Name],

Thanks for reaching out. I'm available for a call next week—would
[day/time options] work for you?

Best,
[Your Name]`,
            followup: `Hi [Name],

Just following up on my previous message. Please let me know if you have any questions or want to schedule time to discuss.

Thanks,
[Your Name]`,
            thankyou: `Hi [Name],

Thank you for your email. I appreciate the update and will follow up with the next steps shortly.

Best,
[Your Name]`,
          };

          const loadTemplate = () => {
            const key = templateSelect.value;
            if (!key) return;
            emailInput.value = templates[key] || "";
            showToast('Template loaded');
          };

          loadTemplateBtn.addEventListener('click', loadTemplate);
          templateSelect.addEventListener('change', loadTemplate);

          const showToast = (message) => {
            toast.textContent = message;
            toast.classList.add('show');
            window.setTimeout(() => toast.classList.remove('show'), 2600);
          };

          const setLoading = (isLoading) => {
            generateBtn.disabled = isLoading;
            clearBtn.disabled = isLoading;
            generateBtn.textContent = isLoading ? 'Generating…' : 'Generate response';
          };

          const formatResponse = (data) => {
            if (typeof data === 'string') return data;
            try {
              return JSON.stringify(data, null, 2);
            } catch {
              return String(data);
            }
          };

          form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const email = emailInput.value.trim();
            if (!email) {
              showToast('Please enter email content before generating.');
              return;
            }

            setLoading(true);
            responseContainer.hidden = true;
            responseText.textContent = '';

            try {
              const res = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
              });

              if (!res.ok) {
                const text = await res.text();
                throw new Error(`Request failed (${res.status}): ${text}`);
              }

              let data;
              try {
                data = await res.json();
              } catch (jsonError) {
                const text = await res.text();
                throw new Error(`Failed to parse JSON response: ${text}`);
              }

              if (data && typeof data === 'object' && 'draft_reply' in data) {
                responseMeta.textContent = data.warning ?? (data.classification ? `Classification: ${data.classification}` : '');
                responseText.textContent = data.draft_reply;
              } else {
                responseMeta.textContent = '';
                responseText.textContent = formatResponse(data);
              }
              responseContainer.hidden = false;
              showToast(data.warning ? data.warning : 'Response generated!');
            } catch (error) {
              responseText.textContent = 'Error: ' + (error.message || error);
              responseContainer.hidden = false;
              showToast('Request failed — check console for details.');
              console.error(error);
            } finally {
              setLoading(false);
            }
          });

          clearBtn.addEventListener('click', () => {
            emailInput.value = '';
            responseContainer.hidden = true;
            responseMeta.textContent = '';
          });

          copyBtn.addEventListener('click', async () => {
            try {
              await navigator.clipboard.writeText(responseText.textContent);
              showToast('Copied to clipboard!');
            } catch (err) {
              showToast('Clipboard copy failed.');
            }
          });
        </script>
      </body>
    </html>
    """


@app.get("/healthz")
def healthz():
    """Health check endpoint for readiness probes."""
    return {"status": "ok"}


@app.post("/generate")
def generate(req: EmailRequest):
    try:
        result = run_agent(req.email)
        return result
    except Exception as e:
        # Log the error and return a consistent JSON error response.
        # This prevents HTML 500 pages from breaking the client-side JSON parsing.
        raise HTTPException(status_code=500, detail=str(e))
