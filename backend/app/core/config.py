import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Settings:
    PROJECT_NAME: str = "TutorIA API"
    API_V1_STR: str = "/api/v1"
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a74e0cd1eceda53ff0b1cd99e67a7e0269cce9eca7a27be3de248d58be9ff54d")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Gemini API Key for Chatbot
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()
