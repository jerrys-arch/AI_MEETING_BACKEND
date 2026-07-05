 AI Meeting Note Generator — Backend

A production-ready FastAPI backend for an AI-powered meeting note generator that supports both English and Amharic languages. The app transcribes audio recordings or accepts text transcripts and generates clean, structured meeting notes with key points, decisions, and action items.


## 🌐 Live Demo

**Frontend:** https://ai-meeting-summerizer-sable.vercel.app/

**Backend API:** https://ai-meeting-backend-dvt7.onrender.com

**API Docs:** https://ai-meeting-backend-dvt7.onrender.com/docs


✨ Features


🎙 Audio Transcription — Upload or record audio (MP3, WAV, WebM) and get accurate transcriptions
📄 Text Summarization — Paste meeting transcripts and get structured notes
🌍 Bilingual Support — Full support for both English and Amharic
🔍 Auto Language Detection — Automatically detects whether the input is English or Amharic
🔐 JWT Authentication — Secure register/login with JWT tokens
🔑 Google OAuth — Sign in with Google
🔒 Forgot Password — Password reset via email
🗄 Meeting History — Save, view, and delete past meeting notes
📄 PDF Export — Download meeting notes as a formatted PDF (with Amharic font support)
✉️ Email Notes — Send meeting notes to attendees via email
🤖 AI-Powered — Uses Groq (Whisper + LLaMA) for English and Google Gemini for Amharic



🛠 Tech Stack

CategoryTechnologyFrameworkFastAPI (Python)English TranscriptionGroq Whisper Large V3Amharic TranscriptionGoogle Gemini 2.5 FlashEnglish SummarizationGroq Qwen 3.6 27BAmharic SummarizationGoogle Gemini 2.5 FlashDatabasePostgreSQL (Supabase) + SQLAlchemyAuthenticationJWT (python-jose) + Google OAuth 2.0EmailResend APIPDF GenerationReportLab (with NotoSansEthiopic font)DeploymentRender


📁 Project Structure

ai_meeting_backend/
├── main.py                      # FastAPI app entry point
├── auth.py                      # JWT authentication logic
├── database.py                  # Database connection setup
├── models.py                    # SQLAlchemy database models
├── schemas.py                   # Pydantic request/response schemas
├── requirements.txt
├── fonts/
│   └── NotoSansEthiopic-Regular.ttf   # Amharic font for PDF
├── routes/
│   ├── auth.py                  # Auth endpoints (register, login, Google OAuth, forgot password)
│   ├── audio.py                 # Audio upload/transcription endpoint
│   ├── text.py                  # Text summarization endpoint
│   └── meetings.py              # Meeting history, PDF export, email endpoints
└── services/
    ├── whisper_service.py       # Audio transcription logic
    ├── summarizer_service.py    # AI summarization logic
    ├── language_detector.py     # Auto language detection
    ├── pdf_service.py           # PDF generation
    └── email_service.py         # Email sending


🚀 API Endpoints

Authentication

MethodEndpointDescriptionPOST/auth/registerCreate a new accountPOST/auth/loginLogin and get JWT tokenGET/auth/meGet current user infoGET/auth/googleSign in with GoogleGET/auth/google/callbackGoogle OAuth callbackPOST/auth/forgot-passwordSend password reset emailPOST/auth/reset-passwordReset password with token

Meeting Notes

MethodEndpointDescriptionPOST/summarize-textSummarize pasted textPOST/summarize-audioUpload audio and get summary

Meeting History

MethodEndpointDescriptionGET/meetings/Get all meetingsGET/meetings/{id}Get single meetingDELETE/meetings/{id}Delete a meetingGET/meetings/{id}/export-pdfDownload PDFPOST/meetings/{id}/send-emailEmail notes to attendees


🔧 Environment Variables

Create a .env file in the project root:

env# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Authentication
SECRET_KEY=your_secret_key_here

# AI Services
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxx

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# App URLs
BACKEND_URL=https://your-backend.onrender.com
FRONTEND_URL=https://your-frontend.vercel.app

# Email
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx


🏃 Running Locally

1. Clone the repository:

bashgit clone https://github.com/jerrys-arch/AI_MEETING_BACKEND.git
cd AI_MEETING_BACKEND

2. Create and activate virtual environment:

bashpython -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

3. Install dependencies:

bashpip install -r requirements.txt

4. Create .env file with the environment variables listed above.

5. Run the server:

bashuvicorn main:app --reload

6. Open API docs:

http://localhost:8000/docs


📊 How It Works

User uploads audio or pastes text
          ↓
Auto-detect language (English or Amharic)
          ↓
    ┌─────┴─────┐
English        Amharic
  ↓               ↓
Groq           Gemini
Whisper        2.5 Flash
(transcribe)   (transcribe)
  ↓               ↓
Groq           Gemini
Qwen3.6        2.5 Flash
(summarize)    (summarize)
  ↓               ↓
    └─────┬─────┘
          ↓
  Structured Meeting Notes
  (Key Points, Decisions, Action Items)
          ↓
  Save to PostgreSQL database
          ↓
  Return to user + optional PDF/Email


📝 Summary Output Format

English:

📋 Key Points:
- Point 1
- Point 2

✅ Decisions Made:
- Decision 1

📌 Action Items:
- Person: Task — deadline

Amharic:

📋 ዋና ነጥቦች:
- ነጥብ 1

✅ ውሳኔዎች:
- ውሳኔ 1

📌 እርምጃዎች:
- ሰው: ተግባር


🔑 Authentication Flow

Regular login:

POST /auth/register → POST /auth/login → receive JWT token
→ include token in all requests: Authorization: Bearer <token>

Google OAuth:

Redirect to /auth/google
→ Google login page
→ /auth/google/callback
→ redirect to frontend /auth/callback?token=<jwt>
→ store token and use for all requests


⚠️ Known Limitations


Email sending — On Resend free tier, emails can only be sent to whitelisted addresses without a verified domain
Free tier sleep — Render free tier sleeps after 15 minutes of inactivity (first request may take 30-50 seconds)
Gemini rate limits — Gemini free tier has 5-15 requests per minute depending on the model



👤 Author

Backend Engineer: Eyerus molla
GitHub: jerrys-arch
