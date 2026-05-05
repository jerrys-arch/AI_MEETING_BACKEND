import os
from groq import Groq
import google.generativeai as genai


def clean_text(text: str) -> str:
    text = text.strip()
    text = text.replace("\n", " ")
    return text


def summarize_english(text: str) -> str:
    """Use Groq LLaMA for English summarization."""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    system_prompt = """You are a professional meeting note taker.
The user will give you a meeting transcript in English.
Generate a clean, structured meeting note IN ENGLISH ONLY.
Do NOT translate. Do NOT add information not in the transcript.
Be concise and professional.

Use this exact format:

📋 Key Points:
• [point]
• [point]

✅ Decisions Made:
• [decision]

📌 Action Items:
• [action item — who does what]

If a section has nothing mentioned, write: • None mentioned"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the meeting transcript:\n\n{text[:4000]}"}
        ],
        max_tokens=600,
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def summarize_amharic(text: str) -> str:
    """Use Gemini for Amharic summarization."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""You are a professional meeting note taker.
The following is an Amharic meeting transcript.
Generate a clean, structured meeting note IN AMHARIC ONLY.
Do NOT translate to English. Only use information from the transcript.

Use this exact format:

📋 ዋና ነጥቦች:
• [ነጥብ]

✅ ውሳኔዎች:
• [ውሳኔ]

📌 እርምጃዎች:
• [እርምጃ]

If a section has nothing, write: • የለም

Transcript:
{text[:4000]}"""

    response = model.generate_content(prompt)
    return response.text.strip()


def summarize_text(text: str, language: str = "en") -> str:
    text = clean_text(text)

    if not text:
        return "No transcription available to summarize."

    if language == "am":
        return summarize_amharic(text)
    else:
        return summarize_english(text)