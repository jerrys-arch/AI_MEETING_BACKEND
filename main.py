from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.audio import router as audio_router
from routes.text import router as text_router
from routes.auth import router as auth_router
from routes.meetings import router as meetings_router

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


@app.on_event("startup")
async def startup():
    """Create tables on startup with error handling so app doesn't crash."""
    try:
        from database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Database startup warning: {e}")
        print("App will continue — database may not be connected.")


@app.get("/")
def root():
    return {"message": "Meeting Note Generator API is running."}