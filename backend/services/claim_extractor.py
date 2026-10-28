from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from backend.config import Config
from backend.services.summarizer import _make_llm, _parse_json
import re


class ClaimExtractor:
    def __init__(self):
        self.llm = _make_llm()

    def extract_claims(self, article_text):
        article_text = article_text[:6000]
        max_claims = Config.MAX_CLAIMS

        prompt_text = """You are a fact-checking expert. Read the following news article and extract the most important verifiable factual claims.

ARTICLE:
{article_text}

Return ONLY a valid JSON object (no markdown, no extra text):
{{
    "claims": [
        {{
            "claim_text": "The exact factual claim as stated in the article.",
            "claim_type": "Statistical|Quote|Event|Policy|Scientific|General",
            "importance": "HIGH|MEDIUM|LOW"
        }}
    ]
}}

RULES:
- Extract at most {max_claims} claims.
- Focus on specific, verifiable factual statements (numbers, names, events, policies).
- Do NOT include opinions, predictions, or vague statements.
- Return ONLY the JSON object, nothing else.
"""
        prompt = PromptTemplate(
            template=prompt_text,
            input_variables=["article_text", "max_claims"]
        )
        chain = prompt | self.llm

        try:
            result = chain.invoke({"article_text": article_text, "max_claims": str(max_claims)})
            content = result.content if hasattr(result, 'content') else str(result)
            parsed = _parse_json(content)
            return parsed.get("claims", [])
        except Exception as e:
            return []
