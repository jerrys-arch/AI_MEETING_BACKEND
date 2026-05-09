from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
import models
from services.summarizer_service import summarize_text
from services.language_detector import detect_language


router = APIRouter()


class TextRequest(BaseModel):
    text: str


def generate_title(summary: str, language: str) -> str:
    """Auto-generate a short title from the first key point in the summary."""
    if not summary:
        return "Untitled Meeting"

    lines = [l.strip() for l in summary.split("\n") if l.strip()]

    found_section = False
    for line in lines:
        if "Key Points" in line or "ዋና ነጥቦች" in line:
            found_section = True
            continue
        if found_section and line.startswith("•"):
            title = line[1:].strip()
            return title[:60] + "..." if len(title) > 60 else title

    for line in lines:
        if line.startswith("•"):
            title = line[1:].strip()
            return title[:60] + "..." if len(title) > 60 else title

    return "Meeting Notes"


@router.post("/summarize-text")
def summarize(
    data: TextRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # Auto detect language
    language = detect_language(data.text)

    # Summarize
    summary = summarize_text(data.text, language=language)

    # Auto-generate title
    title = generate_title(summary, language)

    # Save to database
    meeting = models.Meeting(
        user_id=current_user.id,
        title=title,
        language=language,
        transcription=data.text,
        summary=summary,
        source="text"
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return {
        "meeting_id": meeting.id,
        "title": title,
        "language": language,
        "summary": summary
    }