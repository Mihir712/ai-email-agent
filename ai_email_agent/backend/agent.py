import os

from .classifier import classify_email
from .draft_generator import generate_draft
from . import database
import importlib


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
        examples = [{"email": e['email'], "reply": e['reply']} for e in examples]

    # ensure at least one example exists
    if not examples:
        examples = [{"email": "Are you free next week?", "reply": "Happy to connect next week."}]

    warning = None
    if not os.getenv("OPENAI_API_KEY"):
        warning = (
            "OPENAI_API_KEY is not set. Returning a fallback response. "
            "Set OPENAI_API_KEY to enable real model generation."
        )

    # generate draft
    draft = generate_draft(email, examples)

    # save draft
    database.save_draft(incoming_id, draft)

    result = {
        "classification": category,
        "draft_reply": draft,
    }

    if warning:
        result["warning"] = warning

    return result