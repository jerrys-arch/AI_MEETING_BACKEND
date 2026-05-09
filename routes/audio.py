from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import os
import uuid

from database import get_db
from auth import get_current_user
import models
from services.whisper_service import transcribe_audio
from services.summarizer_service import summarize_text

router = APIRouter()

UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "audio/mpeg", "audio/wav", "audio/x-wav",
    "audio/mp3", "audio/webm", "audio/ogg"
}


def generate_title(summary: str, language: str) -> str:
    """Auto-generate a short title from the first key point in the summary."""
    if not summary:
        return "Untitled Meeting"

    lines = [l.strip() for l in summary.split("\n") if l.strip()]

    # Find first bullet point after Key Points / ዋና ነጥቦች
    found_section = False
    for line in lines:
        if "Key Points" in line or "ዋና ነጥቦች" in line:
            found_section = True
            continue
        if found_section and line.startswith("•"):
            title = line[1:].strip()
            # Truncate to 60 chars
            return title[:60] + "..." if len(title) > 60 else title

    # Fallback — use first bullet point anywhere
    for line in lines:
        if line.startswith("•"):
            title = line[1:].strip()
            return title[:60] + "..." if len(title) > 60 else title

    return "Meeting Notes"


@router.post("/summarize-audio")
async def summarize_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use mp3, wav, or webm."
        )

    file_ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        # Step 1: Transcribe + detect language
        transcription, language = transcribe_audio(file_path)

        if not transcription:
            return {
                "language": "unknown",
                "transcription": "",
                "summary": "Transcription failed. Check audio quality."
            }

        # Step 2: Summarize
        summary = summarize_text(transcription, language=language)

        # Step 3: Auto-generate title
        title = generate_title(summary, language)

        # Step 4: Save to database
        meeting = models.Meeting(
            user_id=current_user.id,
            title=title,
            language=language,
            transcription=transcription,
            summary=summary,
            source="audio_upload"
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        return {
            "meeting_id": meeting.id,
            "title": title,
            "language": language,
            "transcription": transcription,
            "summary": summary
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)