import os
from groq import Groq
import google.generativeai as genai
from services.language_detector import detect_language


def transcribe_amharic(file_path: str) -> str:
    """Use Gemini 2.5 Flash to transcribe Amharic audio."""
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        audio_file = genai.upload_file(file_path)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            audio_file,
            "Please transcribe this Amharic audio exactly as spoken. Return only the transcribed text, nothing else."
        ])
        text = response.text.strip()
        print("TRANSCRIBED TEXT [am]:", text)
        genai.delete_file(audio_file.name)
        return text
    except Exception as e:
        print("GEMINI TRANSCRIPTION ERROR:", str(e))
        return ""


def transcribe_english(file_path: str) -> str:
    """Use Groq Whisper for English transcription."""
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="text",
            )
        text = transcription.strip()
        print("TRANSCRIBED TEXT [en]:", text)
        return text
    except Exception as e:
        print("GROQ TRANSCRIPTION ERROR:", str(e))
        return ""


def transcribe_audio(file_path: str, language: str = "auto") -> tuple[str, str]:
    """
    Transcribe audio and return (transcription, detected_language).
    If language="auto", transcribe with Groq first (fast), then detect language.
    If Amharic detected, re-transcribe with Gemini for accuracy.
    """
    if language == "am":
        return transcribe_amharic(file_path), "am"

    if language == "en":
        return transcribe_english(file_path), "en"

    # AUTO DETECT:
    # Step 1: Transcribe with Groq (fast, handles both languages roughly)
    text = transcribe_english(file_path)

    # Step 2: Detect language from transcription
    detected = detect_language(text)

    # Step 3: If Amharic detected, re-transcribe with Gemini for accuracy
    if detected == "am":
        print("Amharic detected — re-transcribing with Gemini...")
        text = transcribe_amharic(file_path)

    return text, detected