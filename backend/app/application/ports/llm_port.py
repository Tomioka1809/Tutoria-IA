from abc import ABC, abstractmethod
from typing import List, Dict

class LLMPort(ABC):
    @abstractmethod
    async def generate_response(self, system_instruction: str, history: List[Dict], user_message: str) -> str:
        """
        Generates a chat response asymmetrically.
        history expects [{"role": "user"|"model", "parts": [{"text": "..."}]}] format or similar.
        """
        pass

    @abstractmethod
    async def compute_embedding(self, text: str) -> List[float]:
        """
        Computes the semantic embedding of a text using a vector model.
        """
        pass
