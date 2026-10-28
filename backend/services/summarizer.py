from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from backend.config import Config
import json
import re


def _make_llm():
    kwargs = dict(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL_NAME,
        temperature=0,
    )
    if Config.OPENAI_BASE_URL:
        kwargs["base_url"] = Config.OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)


def _parse_json(content):
    """Robustly parse JSON from LLM response, stripping markdown fences."""
    content = content.strip()
    # Strip ```json ... ``` or ``` ... ```
    if content.startswith("```"):
        parts = content.split("```")
        # parts[1] is the content between first pair of ```
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
        raise ValueError(f"Could not parse JSON from response:\n{content[:300]}")


class Summarizer:
    def __init__(self):
        self.llm = _make_llm()

    def summarize(self, article_text):
        article_text = article_text[:8000]

        prompt_text = """You are an expert news summarizer. Read the following article and provide a structured summary.

ARTICLE:
{article_text}

Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
{{
    "summary": "A 3-5 sentence summary of the article.",
    "key_points": ["Key point 1", "Key point 2", "Key point 3", "Key point 4", "Key point 5"],
    "main_topic": "The primary topic",
    "entities": ["Entity1", "Entity2"]
}}

RULES:
- Do not invent information not in the article.
- Return ONLY the JSON object, nothing else.
"""
        prompt = PromptTemplate(template=prompt_text, input_variables=["article_text"])
        chain = prompt | self.llm

        try:
            result = chain.invoke({"article_text": article_text})
            content = result.content if hasattr(result, 'content') else str(result)
            return _parse_json(content)
        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")
