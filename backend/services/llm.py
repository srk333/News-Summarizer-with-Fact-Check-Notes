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


def get_client():
    global _client
    if _client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMError("OPENAI_API_KEY is missing. Add it to your .env file.")
        _client = OpenAI(api_key=key, base_url=os.getenv("OPENAI_BASE_URL") or None)
    return _client


def _with_retry(fn, tries=4):
    delay = 4
    for attempt in range(tries):
        try:
            return fn()
        except RateLimitError:
            if attempt == tries - 1:
                raise LLMError("Rate limit reached on the free tier. Wait a minute and try again.")
            time.sleep(delay)
            delay *= 2
        except APIConnectionError as e:
            raise LLMError(f"Could not reach the AI service: {e}")
        except APIStatusError as e:
            if e.status_code in (401, 403):
                raise LLMError("API key rejected. Check OPENAI_API_KEY and OPENAI_BASE_URL in .env.")
            if e.status_code == 404:
                raise LLMError("Model not found. Check OPENAI_MODEL_NAME / EMBEDDING_MODEL_NAME in .env.")
            if e.status_code >= 500 and attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise LLMError(f"AI service error ({e.status_code}): {e}")


def chat(system, user, temperature=0.1):
    model = os.getenv("OPENAI_MODEL_NAME", "gemini-2.5-flash-lite")

    def call():
        r = get_client().chat.completions.create(
            model=model, temperature=temperature,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}])
        return r.choices[0].message.content or ""

    return _with_retry(call)


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

        vectors.extend(_with_retry(call))
    return np.array(vectors, dtype="float32")