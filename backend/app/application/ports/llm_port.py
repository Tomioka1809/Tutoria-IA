from abc import ABC, abstractmethod
from typing import List, Dict

class LLMPort(ABC):
    @abstractmethod
    async def generate_response(
        self, 
        system_instruction: str, 
        history: List[Dict], 
        user_message: str,
        tools: List = None
    ) -> str:
        """
        Generates a chat response asymmetrically.
        history expects [{"role": "user"|"model", "parts": [{"text": "..."}]}] format or similar.
        """
        pass

    @abstractmethod
    async def compute_embedding(
        self,
        text: str,
        task_type: str = "RETRIEVAL_QUERY",
    ) -> List[float]:
        """
        Computes the semantic embedding of a text using a vector model.

        task_type distingue los dos lados de una busqueda asimetrica: los
        fragmentos del corpus se indexan con RETRIEVAL_DOCUMENT y la consulta del
        usuario se embebe con RETRIEVAL_QUERY. Usar el mismo modo para ambos trata
        una pregunta corta y un documento largo como si fueran comparables entre
        si, lo que degrada la recuperacion.

        El valor por defecto es RETRIEVAL_QUERY porque en tiempo de ejecucion el
        unico texto que se embebe es la consulta; la indexacion lo pasa explicito.
        """
        pass
