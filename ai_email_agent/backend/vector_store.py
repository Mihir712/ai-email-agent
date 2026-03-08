from typing import List, Dict
import logging

from . import database

logger = logging.getLogger(__name__)


# Try to import chromadb lazily; keep module import-safe if chromadb or its deps
# are incompatible with the runtime (e.g., Pydantic v1 vs Python 3.14 issues).
try:
    import chromadb
    CHROMA_AVAILABLE = True
except Exception as e:
    logger.warning("ChromaDB import failed or is incompatible: %s", e)
    CHROMA_AVAILABLE = False


def build_collection():
    if not CHROMA_AVAILABLE:
        return None

    try:
        client = chromadb.Client()
        try:
            collection = client.get_collection("emails")
        except Exception:
            collection = client.create_collection("emails")

        training = database.get_training_emails()
        if len(training) == 0:
            return collection

        existing = collection.count()
        if existing >= len(training):
            return collection

        docs = [t['email'] for t in training]
        metadatas = [{"reply": t['reply'], "category": t['category']} for t in training]
        ids = [str(t['id']) for t in training]

        collection.add(documents=docs, metadatas=metadatas, ids=ids)
        return collection
    except Exception as e:
        logger.exception("failed building chroma collection: %s", e)
        return None


def search_similar(text: str, n_results: int = 3) -> List[Dict]:
    """Return list of examples with keys `email` and `reply`.

    If Chroma is unavailable, fall back to a simple DB substring scoring.
    """
    if CHROMA_AVAILABLE:
        try:
            client = chromadb.Client()
            try:
                collection = client.get_collection("emails")
            except Exception:
                collection = client.create_collection("emails")

            res = collection.query(query_texts=[text], n_results=n_results, include=["documents", "metadatas"])
            results = []
            docs = res.get('documents', [[]])[0]
            metas = res.get('metadatas', [[]])[0]
            for d, m in zip(docs, metas):
                results.append({"email": d, "reply": m.get('reply') if isinstance(m, dict) else None})
            return results
        except Exception as e:
            logger.exception("Chroma query failed, falling back to DB: %s", e)

    # Fallback: simple DB-based nearest by substring
    training = database.get_training_emails()
    lowered = text.lower()
    scored = []
    for t in training:
        score = 0
        for tok in lowered.split():
            if tok in (t['email'] or '').lower():
                score += 1
        if score > 0:
            scored.append((score, t))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [{"email": s[1]['email'], "reply": s[1]['reply']} for s in scored[:n_results]]


# Build collection if possible (best-effort)
try:
    build_collection()
except Exception:
    pass