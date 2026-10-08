import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    # Default to SQLite if DATABASE_URL is not set so tests can run locally without Postgres
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///newslens.db')
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'dummy-openai-key')
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', 'dummy-tavily-key')
    OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')
