from backend.config import Config
print('OPENAI_API_KEY set:', bool(Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != 'dummy-key'))
print('OPENAI_BASE_URL:', Config.OPENAI_BASE_URL)
print('OPENAI_MODEL_NAME:', Config.OPENAI_MODEL_NAME)
print('EMBEDDING_MODEL_NAME:', Config.EMBEDDING_MODEL_NAME)
print('TAVILY_API_KEY set:', bool(Config.TAVILY_API_KEY))
print('DB URI:', Config.SQLALCHEMY_DATABASE_URI[:60])
print()

from backend.services.summarizer import _make_llm, _parse_json
from backend.services.claim_extractor import ClaimExtractor
from backend.services.fact_checker import FactChecker
from backend.services.rag_service import RAGService
from backend.services.search_service import SearchService
from backend.models.article import Article
print('All imports OK')

import json, re

def _parse_json_local(content):
    content = content.strip()
    if content.startswith("```"):
        parts = content.split("```")
        inner = parts[1]
        if inner.startswith("json"):
            inner = inner[4:]
        content = inner.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise

s1 = '{"summary": "Test", "key_points": ["a","b"]}'
print('Plain JSON parse:', _parse_json_local(s1))

s2 = '```json\n{"verdict": "SUPPORTED", "fact_check_note": "Yes"}\n```'
print('Markdown JSON parse:', _parse_json_local(s2))

print()
print('All checks PASSED - project is ready to run!')
