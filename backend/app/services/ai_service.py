from typing import List
from app.services.llm_factory import LLMFactory

def generate_code_suggestion(messages: List[dict], model: str = "ollama") -> str:
    """
    Delegates to the appropriate LLM backend based on the selected model.
    """
    result = LLMFactory.generate_response(messages, model)
    return result
