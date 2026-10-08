from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.config import Config

class FactChecker:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY, 
            model=Config.OPENAI_MODEL_NAME, 
            temperature=0
        )
        
    def check_claim(self, claim_text, evidence_list):
        parser = JsonOutputParser()
        
        # Combine evidence text
        evidence_text = ""
        for i, ev in enumerate(evidence_list):
            evidence_text += f"\nSource {i+1} ({ev['domain']}):\n{ev['text']}\n"
            
        if not evidence_text.strip():
            # No evidence found
            return {
                "verdict": "INSUFFICIENT EVIDENCE",
                "fact_check_note": "No external evidence could be found to verify this claim."
            }

        prompt = PromptTemplate(
            template="""
            You are an expert fact-checker. Determine if the ARTICLE CLAIM is supported by the EXTERNAL EVIDENCE.
            
            ARTICLE CLAIM:
            {claim_text}
            
            EXTERNAL EVIDENCE:
            {evidence_text}
            
            Provide the output in the following JSON format:
            {{
                "verdict": "SUPPORTED, PARTIALLY SUPPORTED, CONTRADICTED, INSUFFICIENT EVIDENCE, or UNABLE TO VERIFY",
                "fact_check_note": "A clear, concise explanation of why this verdict was chosen, citing the provided evidence."
            }}
            
            RULES:
            - NEVER use your internal knowledge. Base your decision ONLY on the provided EXTERNAL EVIDENCE.
            - If the evidence does not relate to the claim, return INSUFFICIENT EVIDENCE.
            - Do not invent sources.
            - DO NOT claim mathematical certainty. Explain in terms of what the sources report.
            
            {format_instructions}
            """,
            input_variables=["claim_text", "evidence_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({
                "claim_text": claim_text,
                "evidence_text": evidence_text
            })
            return result
        except Exception as e:
            return {
                "verdict": "UNABLE TO VERIFY",
                "fact_check_note": f"Fact-checking engine encountered an error: {str(e)}"
            }
