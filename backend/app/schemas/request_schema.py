from pydantic import BaseModel, Field

class CodePrompt(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=2000, description="Prompt or code snippet for AI processing")
    model: str | None = Field(default="ollama", description="Optional model name (ollama, openai, etc.)")
