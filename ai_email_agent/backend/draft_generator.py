import logging
import os

from .local_llm import LocalModelError, generate_with_local_model
from openai import OpenAI

logger = logging.getLogger(__name__)


FALLBACK_DRAFT = (
    "Hi — thanks for reaching out. I'd be happy to coordinate a time to meet. "
    "Please share a few time slots that work for you this week, or let me know your timezone."
)


def generate_draft(email, examples):
    example_text = ""

    for e in examples:
        example_text += f"Email: {e.get('email')}\nReply: {e.get('reply')}\n\n"

    prompt = f"""
Write a reply email in the same tone as these examples.

{example_text}

Incoming email:
{email}

Rules:
Max 150 words
Professional
Clear next step
"""

    use_local = os.getenv("LOCAL_LLM", "").lower() in ("1", "true", "yes")
    if use_local:
        try:
            return generate_with_local_model(prompt, max_tokens=500)
        except LocalModelError as e:
            # Local model generation can fail intermittently (e.g., empty response).
            # Fall back to a safe canned reply so the app stays usable.
            logger.exception("Local LLM generation failed; using fallback draft")
            return FALLBACK_DRAFT
        except Exception as e:
            logger.exception("Local LLM generation failed")
            raise RuntimeError(f"Local LLM generation failed: {e}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set this environment variable to enable model generation, "
            "or set LOCAL_LLM=1 and install a local model."
        )

    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.exception("LLM generation failed")
        raise RuntimeError(f"LLM generation failed: {e}")
