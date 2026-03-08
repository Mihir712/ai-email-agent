"""Local LLM helper (optional, for running without OpenAI)."""

import logging
import os

logger = logging.getLogger(__name__)


class LocalModelError(RuntimeError):
    pass


def generate_with_local_model(prompt: str, max_tokens: int = 500) -> str:
    """Generate a response using a locally-hosted LLM.

    This function is intentionally lightweight: it tries multiple local model
    backends (gpt4all, llama_cpp) and raises a clear error if none are available.

    Set the following env vars to control behavior:
      - LOCAL_LLM=1 (or true/yes) to enable local generation
      - LOCAL_MODEL_PATH=/path/to/model.ggml (optional)
      - LOCAL_MODEL_NAME=ggml-gpt4all-j-v1.3-groovy (optional; used if path is unset)
    """

    model_path = os.getenv("LOCAL_MODEL_PATH")
    model_name = os.getenv("LOCAL_MODEL_NAME")

    # If the user provided a local model file that llama_cpp supports, prefer llama_cpp.
    # llama_cpp supports .ggml and .gguf files (and similar packed formats), while gpt4all expects a model directory.
    prefer_llama = model_path and model_path.lower().endswith((".ggml", ".gguf"))

    if prefer_llama:
        try:
            from llama_cpp import Llama  # type: ignore

            logger.info("Using llama_cpp local model (ggml): %s", model_path)
            llm = Llama(model_path=model_path)

            # Try once, and if we get an empty response, retry with a smaller context size.
            # Some local models can return empty output if the context window is too large.
            for attempt, tokens in enumerate((max_tokens, min(max_tokens, 256)), start=1):
                resp = llm(prompt, max_tokens=tokens)
                # log for debugging if the response is not usable
                logger.debug("llama_cpp response (attempt %d): %s", attempt, resp)
                text = resp.get("choices", [{}])[0].get("text")
                if text:
                    return text

            raise LocalModelError(
                "llama_cpp returned an empty response after retrying with smaller max_tokens. "
                "Try a different model file, or set a smaller LOCAL_MAX_TOKENS value."
            )
        except ImportError:
            # Fail fast if we know the user is pointing at a .ggml file but llama_cpp isn't installed.
            raise LocalModelError(
                "Local .ggml model detected, but llama_cpp is not installed. "
                "Install it with: python3 -m pip install llama-cpp-python"
            )
        except Exception as e:
            msg = str(e)
            if "Failed to load model from file" in msg:
                raise LocalModelError(
                    "Failed to load the .ggml file with llama_cpp. "
                    "Try downloading a .gguf model instead (e.g. from https://gpt4all.io/models) "
                    "and set LOCAL_MODEL_PATH to the .gguf file."
                )
            raise LocalModelError(f"Local model generation failed (llama_cpp): {e}")

    # Prefer gpt4all if installed
    try:
        from gpt4all import GPT4All  # type: ignore

        model_arg = model_path or model_name or "ggml-gpt4all-j-v1.3-groovy"
        logger.info("Using gpt4all local model: %s", model_arg)

        # If the user provided a file path, confirm it exists before passing to gpt4all.
        if model_path:
            if not os.path.exists(model_path):
                raise LocalModelError(
                    f"LOCAL_MODEL_PATH is set to '{model_path}', but that file does not exist. "
                    "Download a local .ggml model and set LOCAL_MODEL_PATH correctly."
                )

        try:
            if model_path:
                # GPT4All requires a positional model_name even when using a local path.
                # Use the provided model_name if present, otherwise derive one from the file.
                model_name_arg = model_name or os.path.splitext(os.path.basename(model_path))[0]
                gpt = GPT4All(model_name_arg, model_path=model_path, allow_download=False)
            else:
                gpt = GPT4All(model_name=model_arg)
        except Exception as e:
            # gpt4all may attempt to download the model & fail with 404.
            msg = str(e)
            if "404" in msg or "Not Found" in msg:
                raise LocalModelError(
                    "gpt4all model not found. The default model name may be unavailable or the download URL changed. "
                    "Set LOCAL_MODEL_PATH to a downloaded model file, or set LOCAL_MODEL_NAME to a different available model."
                )
            raise LocalModelError(f"Failed to load gpt4all model '{model_arg}': {e}")

        # gpt4all uses `n_predict` internally; max_tokens has been supported in newer
        # versions but we guard just in case.
        try:
            return gpt.generate(prompt, max_tokens=max_tokens)
        except TypeError:
            return gpt.generate(prompt, n_predict=max_tokens)

    except ImportError:
        logger.debug("gpt4all not installed; trying llama_cpp")

    # Fallback to llama_cpp if available
    try:
        from llama_cpp import Llama  # type: ignore

        model_arg = model_path or model_name
        if not model_arg:
            raise LocalModelError(
                "No local model path/name set. Set LOCAL_MODEL_PATH or LOCAL_MODEL_NAME."
            )

        logger.info("Using llama_cpp local model: %s", model_arg)
        llm = Llama(model_path=model_arg)
        resp = llm(prompt, max_tokens=max_tokens)
        # llama_cpp returns a dict with choices[0].text
        text = resp.get("choices", [{}])[0].get("text")
        if not text:
            raise LocalModelError("llama_cpp returned an empty response")
        return text

    except ImportError:
        raise LocalModelError(
            "Local LLM requested, but neither gpt4all nor llama_cpp is installed. "
            "Install one of these packages and retry."
        )

    except Exception as e:
        raise LocalModelError(f"Local model generation failed: {e}")
