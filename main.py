from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes.audio import router as audio_router
from routes.text import router as text_router
from routes.auth import router as auth_router
from routes.meetings import router as meetings_router

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Note Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(meetings_router)
app.include_router(audio_router)
app.include_router(text_router)

@app.get("/")
def root():
    return {"message": "Meeting Note Generator API is running."}