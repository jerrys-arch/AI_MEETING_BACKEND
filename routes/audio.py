from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid

from services.whisper_service import transcribe_audio
from services.summarizer_service import summarize_text

router = APIRouter()

UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "audio/mpeg", "audio/wav", "audio/x-wav",
    "audio/mp3", "audio/webm", "audio/ogg"
}

@router.post("/summarize-audio")
async def summarize_audio(file: UploadFile = File(...)):

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use mp3, wav, or webm."
        )

    # Save to temp file with unique name
    file_ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        # Step 1: Audio → Text + detect language
        transcription, language = transcribe_audio(file_path)

        if not transcription:
            return {
                "language": "unknown",
                "transcription": "",
                "summary": "Transcription failed. Check audio quality."
            }

        # Step 2: Text → Summary in detected language
        summary = summarize_text(transcription, language=language)

        return {
            "language": language,
            "transcription": transcription,
            "summary": summary
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Always clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)