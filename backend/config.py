import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)


def _db_url():
    url = os.getenv("DATABASE_URL") or f"sqlite:///{ROOT / 'newslens.db'}"
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        url = f"sqlite:///{ROOT / url.replace('sqlite:///', '')}"
    return url


class Config:
    SQLALCHEMY_DATABASE_URI = _db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CLAIMS = int(os.getenv("MAX_CLAIMS", "5"))
    MAX_ARTICLE_CHARS = 12000

    # LLM / OpenAI-compatible settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)       # None = default OpenAI endpoint
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")

    # Tavily search
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
