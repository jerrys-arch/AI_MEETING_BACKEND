from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.audio import router as audio_router
from routes.text import router as text_router

# ──────────────────────────────────────────────
# APP SETUP
# ──────────────────────────────────────────────
app = FastAPI(title="Meeting Note Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────
app.include_router(audio_router)
app.include_router(text_router)

@app.get("/")
def root():
    return {"message": "Meeting Note Generator API is running."}