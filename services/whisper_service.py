import os
import time
from groq import Groq
from google import genai
from google.genai import types
from services.language_detector import detect_language

GROQ_MAX_BYTES = 25 * 1024 * 1024  # 25MB
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]

# Common English words to check if transcription is real English
ENGLISH_COMMON_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "up", "about", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "not", "only", "same", "so", "than", "too", "very", "just", "but",
    "and", "or", "if", "this", "that", "these", "those", "i", "you", "he",
    "she", "it", "we", "they", "what", "which", "who", "whom", "I", "we",
    "meeting", "team", "project", "work", "time", "good", "new", "first",
    "last", "long", "great", "little", "own", "right", "old", "big", "high",
    "different", "small", "large", "next", "early", "young", "important",
    "public", "private", "real", "best", "free", "think", "know", "take",
    "see", "come", "want", "look", "use", "find", "give", "tell", "ask",
    "seem", "feel", "try", "leave", "call", "keep", "let", "begin", "show",
    "hear", "play", "run", "move", "live", "believe", "hold", "bring", "happen",
    "write", "provide", "sit", "stand", "lose", "pay", "meet", "include",
    "continue", "set", "learn", "change", "lead", "understand", "watch",
    "follow", "stop", "create", "speak", "read", "spend", "grow", "open",
    "walk", "win", "offer", "remember", "love", "consider", "appear", "buy",
    "wait", "serve", "die", "send", "expect", "build", "stay", "fall",
    "cut", "reach", "kill", "remain", "suggest", "raise", "pass", "sell",
    "require", "report", "decide", "pull", "yes", "okay", "um", "uh", "yeah"
}


def looks_like_english(text: str) -> bool:
    """
    Check if text is actually English by seeing how many common
    English words appear. If less than 5% of words are common English
    words, it's probably not English.
    """
    if not text:
        return False

    words = [w.lower().strip(".,!?;:\"'") for w in text.split()]
    if len(words) < 5:
        return False

    english_word_count = sum(1 for w in words if w in ENGLISH_COMMON_WORDS)
    ratio = english_word_count / len(words)

    print(f"English word ratio: {ratio:.2f} ({english_word_count}/{len(words)} common words)")
    return ratio >= 0.05  # at least 5% must be common English words


def transcribe_with_gemini(file_path: str, language_hint: str = None) -> tuple[str, str]:
    """Use Gemini to transcribe audio with retry and model fallback."""
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    ext = file_path.split(".")[-1].lower()
    mime_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "webm": "audio/webm",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
    }
    mime_type = mime_map.get(ext, "audio/wav")

    instruction = (
        "Please transcribe this Amharic audio exactly as spoken. Return only the transcribed text, nothing else."
        if language_hint == "am"
        else "Please transcribe this audio exactly as spoken. Return only the transcribed text, nothing else."
    )

    for model_name in GEMINI_MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                        instruction
                    ]
                )
                text = response.text.strip()
                detected = detect_language(text)
                print(f"TRANSCRIBED TEXT ({model_name}) [{detected}]:", text[:100], "...")
                return text, detected

            except Exception as e:
                error_str = str(e)
                if "503" in error_str or "UNAVAILABLE" in error_str:
                    wait = 10 * (attempt + 1)
                    print(f"Gemini {model_name} unavailable. Waiting {wait}s (attempt {attempt+1}/3)...")
                    time.sleep(wait)
                elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print(f"Gemini {model_name} rate limited — trying next model...")
                    break
                else:
                    print(f"GEMINI TRANSCRIPTION ERROR ({model_name}):", error_str)
                    break

    print("All Gemini models failed.")
    return "", "en"


def transcribe_with_groq(file_path: str) -> str:
    """Use Groq Whisper for transcription. Only for files under 25MB."""
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="text",
            )
        text = transcription.strip()
        print("TRANSCRIBED TEXT [groq]:", text[:100], "...")
        return text
    except Exception as e:
        print("GROQ TRANSCRIPTION ERROR:", str(e))
        return ""


def is_purely_garbage(text: str) -> bool:
    """Check if transcription is clearly garbage."""
    if not text or len(text.split()) < 3:
        return True

    garbage_chars = sum(1 for c in text if (
        '\uAC00' <= c <= '\uD7A3' or  # Korean
        '\u0400' <= c <= '\u04FF' or  # Cyrillic
        '\u3040' <= c <= '\u30FF' or  # Japanese
        '\u4E00' <= c <= '\u9FFF'     # Chinese
    ))

    return (garbage_chars / max(len(text), 1)) > 0.40


def transcribe_audio(file_path: str, language: str = "auto") -> tuple[str, str]:
    """
    Transcribe audio and return (transcription, detected_language).
    """
    file_size = os.path.getsize(file_path)
    is_large_file = file_size > GROQ_MAX_BYTES

    if is_large_file:
        print(f"File size {file_size/1024/1024:.1f}MB exceeds Groq limit — using Gemini...")
        return transcribe_with_gemini(file_path, language_hint=language if language != "auto" else None)

    if language == "am":
        text, _ = transcribe_with_gemini(file_path, language_hint="am")
        return text, "am"

    if language == "en":
        text = transcribe_with_groq(file_path)
        return text, "en"

    # AUTO DETECT
    text = transcribe_with_groq(file_path)

    # Check 1: obvious garbage (Korean, Cyrillic etc)
    if is_purely_garbage(text):
        print("Groq returned garbage script — trying Gemini...")
        return transcribe_with_gemini(file_path)

    # Check 2: Ethiopic characters detected
    detected = detect_language(text)
    if detected == "am":
        print("Amharic detected — re-transcribing with Gemini...")
        text, _ = transcribe_with_gemini(file_path, language_hint="am")
        return text, "am"

    # Check 3: romanized non-English (Groq hallucinating Amharic as Latin)
    if not looks_like_english(text):
        print("Text doesn't look like English — trying Gemini for Amharic...")
        amharic_text, _ = transcribe_with_gemini(file_path, language_hint="am")
        if amharic_text:
            return amharic_text, "am"

    return text, "en"