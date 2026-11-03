import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

# SQLite lives OUTSIDE the project folder, because OneDrive locks files it is syncing
DB_DIR = Path.home() / ".newslens"


def _db_url():
    url = os.getenv("DATABASE_URL", "").strip()

    # PostgreSQL or any non-SQLite database: use as given
    if url and not url.startswith("sqlite"):
        return url

    prefix = "sqlite:///"
    if url.startswith(prefix) and len(url) > len(prefix):
        path = Path(url[len(prefix):])
        if not path.is_absolute():          # e.g. sqlite:///newslens.db
            path = DB_DIR / path.name
    else:
        path = DB_DIR / "newslens.db"

    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.as_posix()}"


class Config:
    SQLALCHEMY_DATABASE_URI = _db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # wait up to 30 s for a lock instead of failing immediately
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 30}}

    MAX_CLAIMS = int(os.getenv("MAX_CLAIMS", "5"))
    MAX_ARTICLE_CHARS = 12000

    # LLM / OpenAI-compatible settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gemini-3.8-flash")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "gemini-embedding-001")

    # Tavily search
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-only-secret-change-me"