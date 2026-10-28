from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from backend.services.summarizer import _make_llm, _parse_json
import re


class FactChecker:
    def __init__(self):
        self.llm = _make_llm()

    def check_claim(self, claim_text, evidence_list):
        if not evidence_list:
            return {
                "verdict": "INSUFFICIENT EVIDENCE",
                "fact_check_note": "No external evidence could be retrieved to verify this claim. This does not mean the claim is false."
            }

        evidence_text = ""
        for i, ev in enumerate(evidence_list):
            src = ev.get('domain', ev.get('source_domain', 'Unknown'))
            txt = ev.get('text', ev.get('evidence_text', ''))[:500]
            evidence_text += f"\nSource {i+1} ({src}):\n{txt}\n"

        prompt_text = """You are an expert fact-checker. Analyze the ARTICLE CLAIM against the EXTERNAL EVIDENCE provided.

ARTICLE CLAIM:
{claim_text}

EXTERNAL EVIDENCE:
{evidence_text}

Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
{{
    "verdict": "SUPPORTED",
    "fact_check_note": "Clear explanation citing the evidence."
}}

The verdict MUST be exactly one of:
- SUPPORTED
- PARTIALLY SUPPORTED
- CONTRADICTED
- INSUFFICIENT EVIDENCE
- UNABLE TO VERIFY

STRICT RULES:
- Base your verdict ONLY on the provided EXTERNAL EVIDENCE above.
- Do NOT use your internal training knowledge.
- If the evidence does not clearly relate to the claim, use INSUFFICIENT EVIDENCE.
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
            return _parse_json(content)
        except Exception as e:
            return {
                "verdict": "UNABLE TO VERIFY",
                "fact_check_note": f"Fact-checking encountered an error: {str(e)}"
            }
