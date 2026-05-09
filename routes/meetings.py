from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, EmailStr
import os

from database import get_db
from auth import get_current_user
import models
import schemas
from services.pdf_services import generate_pdf
from services.email_services import send_meeting_email

router = APIRouter(prefix="/meetings", tags=["Meetings"])


class EmailRequest(BaseModel):
    attendees: List[EmailStr]
    attach_pdf: bool = True


@router.get("/", response_model=List[schemas.MeetingResponse])
def get_all_meetings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all meetings for the logged in user."""
    meetings = db.query(models.Meeting)\
        .filter(models.Meeting.user_id == current_user.id)\
        .order_by(models.Meeting.created_at.desc())\
        .all()
    return meetings


@router.get("/{meeting_id}", response_model=schemas.MeetingResponse)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a single meeting by ID."""
    meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.user_id == current_user.id
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return meeting


@router.delete("/{meeting_id}")
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a meeting."""
    meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.user_id == current_user.id
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    db.delete(meeting)
    db.commit()
    return {"message": "Meeting deleted successfully."}


@router.get("/{meeting_id}/export-pdf")
def export_pdf(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Export meeting notes as PDF."""
    meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.user_id == current_user.id
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    pdf_path = generate_pdf(meeting)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"meeting_{meeting.id}_notes.pdf",
        background=None
    )


@router.post("/{meeting_id}/send-email")
def send_email(
    meeting_id: int,
    data: EmailRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Send meeting notes to a list of attendees via email.
    Optionally attach the PDF.
    """
    meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.user_id == current_user.id
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    # Generate PDF if requested
    pdf_path = None
    if data.attach_pdf:
        pdf_path = generate_pdf(meeting)

    # Send email
    result = send_meeting_email(
        meeting=meeting,
        attendees=data.attendees,
        pdf_path=pdf_path
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {"message": result["message"]}