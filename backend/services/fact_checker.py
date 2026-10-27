from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from backend.config import Config
import json
import re

class FactChecker:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL_NAME,
            temperature=0
        )

    def check_claim(self, claim_text, evidence_list):
        if not evidence_list:
            return {
                "verdict": "INSUFFICIENT EVIDENCE",
                "fact_check_note": "No external evidence could be retrieved to verify this claim. This does not mean the claim is false."
            }

        evidence_text = ""
        for i, ev in enumerate(evidence_list):
            evidence_text += f"\nSource {i+1} ({ev.get('domain','Unknown')}):\n{ev.get('text','')[:500]}\n"

        prompt_text = """
You are an expert fact-checker. Analyze the ARTICLE CLAIM against the EXTERNAL EVIDENCE provided.

ARTICLE CLAIM:
{claim_text}

EXTERNAL EVIDENCE:
{evidence_text}

Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
{{
    "verdict": "SUPPORTED",
    "fact_check_note": "Clear explanation citing the evidence."
}}

The verdict MUST be exactly one of these options:
- SUPPORTED
- PARTIALLY SUPPORTED
- CONTRADICTED
- INSUFFICIENT EVIDENCE
- UNABLE TO VERIFY

STRICT RULES:
- Base your verdict ONLY on the provided EXTERNAL EVIDENCE above.
- Do NOT use your internal training knowledge.
- If the evidence does not clearly relate to the claim, use INSUFFICIENT EVIDENCE.
- Do NOT invent or assume sources.
- Return ONLY the JSON object, nothing else.
"""
        prompt = PromptTemplate(
            template=prompt_text,
            input_variables=["claim_text", "evidence_text"]
        )

        chain = prompt | self.llm

        try:
            result = chain.invoke({"claim_text": claim_text, "evidence_text": evidence_text})
            content = result.content if hasattr(result, 'content') else str(result)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {
                "verdict": "UNABLE TO VERIFY",
                "fact_check_note": "Could not parse the fact-check result."
            }
        except Exception as e:
            return {
                "verdict": "UNABLE TO VERIFY",
                "fact_check_note": f"Fact-checking encountered an error: {str(e)}"
            }
