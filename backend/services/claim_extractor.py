from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.config import Config

class ClaimExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY, 
            model=Config.OPENAI_MODEL_NAME, 
            temperature=0
        )
        
    def extract_claims(self, article_text):
        parser = JsonOutputParser()
        
        prompt = PromptTemplate(
            template="""
            You are an expert fact-checker. Read the following article and extract important factual claims.
            
            ARTICLE:
            {article_text}
            
            Provide the output in the following JSON format:
            {{
                "claims": [
                    {{
                        "claim_text": "Exact text of the claim or simplified version",
                        "claim_type": "Type of claim (e.g., Economic statistic, Quote, Event)",
                        "importance": "HIGH or MEDIUM",
                        "entities_involved": ["Entity1", "Entity2"],
                        "date_time": "Date/time if mentioned, else null"
                    }}
                ]
            }}
            
            RULES:
            - Extract only FACTUAL claims (things that can be verified as true or false).
            - DO NOT treat opinions as factual claims. (e.g., "This is the best economic policy" is an opinion).
            - Focus only on HIGH or MEDIUM importance claims. Ignore trivial details.
            - Extract a maximum of 5 most important claims.
            
            {format_instructions}
            """,
            input_variables=["article_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({"article_text": article_text})
            return result.get("claims", [])
        except Exception as e:
            raise Exception(f"Claim extraction failed: {str(e)}")
