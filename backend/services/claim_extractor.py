from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from backend.config import Config
import json
import re

class ClaimExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL_NAME,
            temperature=0
        )

    def extract_claims(self, article_text):
        article_text = article_text[:6000]

        prompt_text = """
You are an expert fact-checker. Read the following article and extract important factual claims.

ARTICLE:
{article_text}

Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
{{
    "claims": [
        {{
            "claim_text": "The exact factual claim",
            "claim_type": "Type (e.g. Economic statistic, Event, Quote, Scientific fact)",
            "importance": "HIGH or MEDIUM",
            "entities_involved": ["Entity1", "Entity2"],
            "date_time": "Date if mentioned or null"
        }}
    ]
}}

RULES:
- Extract only FACTUAL claims that can be verified as true or false.
- DO NOT include opinions or subjective statements.
- Maximum 5 most important claims.
- Return ONLY the JSON object, nothing else.
"""
        prompt = PromptTemplate(
            template=prompt_text,
            input_variables=["article_text"]
        )

        chain = prompt | self.llm

        try:
            result = chain.invoke({"article_text": article_text})
            content = result.content if hasattr(result, 'content') else str(result)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            parsed = json.loads(content)
            return parsed.get("claims", [])
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed.get("claims", [])
            return []
        except Exception as e:
            raise Exception(f"Claim extraction failed: {str(e)}")
