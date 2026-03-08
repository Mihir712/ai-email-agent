import importlib

from .classifier import classify_email
from .draft_generator import generate_draft
from . import database
from .config import OPENAI_API_KEY, APP_ENV


def run_agent(email: str) -> dict:
    # classify
    category = classify_email(email)

    # save incoming email
    incoming_id = database.save_incoming(email, category)

    # find similar examples from vector store (import lazily)
    try:
        vector_store = importlib.import_module("backend.vector_store")
        examples = vector_store.search_similar(email, n_results=3)
    except Exception:
        examples = database.get_training_emails()
        # normalize shape
        examples = [{"email": e["email"], "reply": e["reply"]} for e in examples]

    # ensure at least one example exists
    if not examples:
        examples = [
            {"email": "Are you free next week?", "reply": "Happy to connect next week."}
        ]

    # If key is missing:
    # - in dev: you could still use a fake/dummy response
    # - in prod: raise so it surfaces as a clean error, not a mixed-in warning
    if not OPENAI_API_KEY:
        if APP_ENV == "development":
            # optional: dev-only fake response
            draft = "FAKE RESPONSE (no OPENAI_API_KEY set in development)."
        else:
            raise RuntimeError("OPENAI_API_KEY is not set.")
    else:
        # generate real draft via OpenAI (your generate_draft should be using OPENAI_API_KEY internally)
        draft = generate_draft(email, examples)

    # save draft
    database.save_draft(incoming_id, draft)

    result = {
        "classification": category,
        "draft_reply": draft,
    }

    return result
