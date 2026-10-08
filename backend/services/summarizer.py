from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.config import Config

class Summarizer:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY, 
            model=Config.OPENAI_MODEL_NAME, 
            temperature=0
        )
        
    def summarize(self, article_text):
        parser = JsonOutputParser()
        
        prompt = PromptTemplate(
            template="""
            You are an expert news summarizer. Read the following article and provide a summary.
            
            ARTICLE:
            {article_text}
            
            Provide the output in the following JSON format:
            {{
                "summary": "A 3-5 sentence short summary of the article.",
                "key_points": [
                    "Key point 1",
                    "Key point 2",
                    "Key point 3",
                    "Key point 4",
                    "Key point 5"
                ],
                "main_topic": "The primary topic of the article",
                "entities": ["Entity1", "Entity2"]
            }}
            
            RULES:
            - Do not invent information that is not present in the article.
            - Ensure the JSON format is strict and parseable.
            
            {format_instructions}
            """,
            input_variables=["article_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({"article_text": article_text})
            return result
        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")
