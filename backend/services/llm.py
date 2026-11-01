import json
import os
import re
import time

import numpy as np
from openai import OpenAI, RateLimitError, APIConnectionError, APIStatusError

import backend.config  # noqa: F401  (loads .env)

_client = None


class LLMError(Exception):
    pass


class LLMBusyError(LLMError):
    """Model overloaded, rate limited, or unavailable: worth trying another model."""
    pass


def get_client():
    global _client
    if _client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMError("OPENAI_API_KEY is missing. Add it to your .env file.")
        _client = OpenAI(
            api_key=key,
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            timeout=60,
            max_retries=0,   # we do our own retrying below
        )
    return _client


def _with_retry(fn, tries=3, base_delay=4):
    """Retry a call on temporary errors; raise LLMBusyError if it stays unavailable."""
    delay = base_delay
    for attempt in range(tries):
        last = attempt == tries - 1
        try:
            return fn()
        except RateLimitError:
            if last:
                raise LLMBusyError("Rate limit reached on the free tier.")
        except APIConnectionError as e:
            if last:
                raise LLMError(f"Could not reach the AI service: {e}")
        except APIStatusError as e:
            code = e.status_code
            if code in (401, 403):
                raise LLMError("API key rejected. Check OPENAI_API_KEY and OPENAI_BASE_URL in .env.")
            if code == 404:
                raise LLMBusyError("Model not found. Check the model names in .env.")
            if code == 429 or code >= 500:
                if last:
                    raise LLMBusyError(f"The AI model is busy right now ({code}).")
            else:
                raise LLMError(f"AI service error ({code}): {e}")
        print(f"[llm] temporary error, retrying in {delay}s (attempt {attempt + 1}/{tries})")
        time.sleep(delay)
        delay *= 2


def _chat_models():
    primary = os.getenv("OPENAI_MODEL_NAME", "gemini-2.5-flash-lite")
    fallback = os.getenv("FALLBACK_MODEL_NAME", "").strip()
    models = [primary]
    if fallback and fallback != primary:
        models.append(fallback)
    return models


def chat(system, user, temperature=0.1):
    last_error = None
    for model in _chat_models():
        def call(m=model):
            r = get_client().chat.completions.create(
                model=m, temperature=temperature,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}])
            return r.choices[0].message.content or ""

        try:
            return _with_retry(call)
        except LLMBusyError as e:
            last_error = e
            print(f"[llm] {model} unavailable ({e}). Trying next model if any.")
    raise LLMError(f"{last_error} Please wait a minute and try again.")


def parse_json(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
        if m:
            return json.loads(m.group(1))
        raise LLMError("The AI returned an unreadable response. Please try again.")


def chat_json(system, user):
    return parse_json(chat(system, user))


def embed(texts, batch_size=50):
    model = os.getenv("EMBEDDING_MODEL_NAME", "gemini-embedding-001")
    vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        def call(b=batch):
            r = get_client().embeddings.create(model=model, input=b)
            return [d.embedding for d in r.data]

        try:
            vectors.extend(_with_retry(call))
        except LLMBusyError as e:
            raise LLMError(f"{e} Please wait a minute and try again.")
    return np.array(vectors, dtype="float32")