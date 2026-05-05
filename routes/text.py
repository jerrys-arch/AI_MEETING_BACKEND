from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.summarizer_service import summarize_text
from services.language_detector import detect_language

router = APIRouter()

class TextRequest(BaseModel):
    text: str

@router.post("/summarize-text")
def summarize(data: TextRequest):

    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # Auto detect language from text
    language = detect_language(data.text)

    # Summarize in detected language
    summary = summarize_text(data.text, language=language)

    return {
        "language": language,
        "summary": summary
    }