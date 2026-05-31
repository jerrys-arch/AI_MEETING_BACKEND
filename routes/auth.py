import os
import httpx
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
import models
import schemas
import auth
from services.email_services import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Auth"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.environ.get("BACKEND_URL", "https://ai-meeting-backend-dvt7.onrender.com")

# In-memory store for reset tokens
# { token: { "email": "...", "expires_at": datetime } }
reset_tokens = {}


# ── Schemas ───────────────────────────────────
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ──────────────────────────────────────────────
# Existing endpoints — unchanged
# ──────────────────────────────────────────────

@router.post("/register", response_model=schemas.UserResponse)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = models.User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=auth.hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not auth.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = auth.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# ──────────────────────────────────────────────
# Forgot Password endpoints
# ──────────────────────────────────────────────

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Send password reset email.
    Always returns success to prevent email enumeration attacks.
    """
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if user and user.hashed_password != "google_oauth":
        # Generate secure reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        # Store token in memory
        reset_tokens[token] = {
            "email": data.email,
            "expires_at": expires_at
        }

        # Send reset email
        send_password_reset_email(data.email, token)

    # Always return success to prevent exposing which emails are registered
    return {"message": "If this email is registered, you will receive a password reset link shortly."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Verify reset token and update password."""

    # Check token exists
    token_data = reset_tokens.get(data.token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    # Check token not expired
    if datetime.utcnow() > token_data["expires_at"]:
        del reset_tokens[data.token]
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")

    # Find user
    user = db.query(models.User).filter(models.User.email == token_data["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Update password
    user.hashed_password = auth.hash_password(data.new_password)
    db.commit()

    # Delete used token
    del reset_tokens[data.token]

    return {"message": "Password reset successfully. You can now log in with your new password."}


# ──────────────────────────────────────────────
# Google OAuth endpoints
# ──────────────────────────────────────────────

@router.get("/google")
async def google_login():
    """Redirect user to Google login page."""
    redirect_uri = f"{BACKEND_URL}/auth/google/callback"
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid email profile"
        "&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google callback, create/find user, return JWT token to frontend."""
    redirect_uri = f"{BACKEND_URL}/auth/google/callback"

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get token from Google.")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google.")

    user_info = user_response.json()
    email = user_info.get("email")
    full_name = user_info.get("name", email)

    if not email:
        raise HTTPException(status_code=400, detail="Could not get email from Google.")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            email=email,
            full_name=full_name,
            hashed_password="google_oauth",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = auth.create_access_token({"sub": user.email})
    return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}")