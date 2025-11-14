from fastapi import APIRouter, HTTPException
from app.schemas.request_schema import CodePrompt
from app.services.ai_service import generate_code_suggestion


router = APIRouter()


@router.post("/suggest-code/")
def suggest_code(data: CodePrompt):
    try:
        result = generate_code_suggestion(data.prompt, data.model)
        if result.startswith("Error"):
            raise HTTPException(status_code=500, detail=result)
        return {"model": data.model, "suggestion": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
