from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.config import Config
import json

class Summarizer:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL_NAME,
            temperature=0
        )

    def summarize(self, article_text):
        # Truncate to avoid token limits
        article_text = article_text[:8000]

        prompt_text = """
You are an expert news summarizer. Read the following article and provide a structured summary.

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
        from langchain.prompts import PromptTemplate
        prompt = PromptTemplate(
            template=prompt_text,
            input_variables=["article_text"]
        )

        chain = prompt | self.llm

        try:
            result = chain.invoke({"article_text": article_text})
            # Parse the content
            content = result.content if hasattr(result, 'content') else str(result)
            # Clean up potential markdown code blocks
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise Exception(f"Summarization failed: Could not parse response as JSON")
        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")
