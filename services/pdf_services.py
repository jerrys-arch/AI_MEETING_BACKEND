import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# Register Amharic font
FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "NotoSansEthiopic-Regular.ttf")
AMHARIC_FONT = "NotoSansEthiopic"

try:
    pdfmetrics.registerFont(TTFont(AMHARIC_FONT, FONT_PATH))
    AMHARIC_FONT_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not load Amharic font: {e}")
    AMHARIC_FONT_AVAILABLE = False


def get_font(language: str) -> str:
    """Return the appropriate font name based on language."""
    if language == "am" and AMHARIC_FONT_AVAILABLE:
        return AMHARIC_FONT
    return "Helvetica"


def generate_pdf(meeting) -> str:
    """Generate a PDF for a meeting and return the file path."""

    pdf_path = os.path.join(TEMP_DIR, f"meeting_{meeting.id}_notes.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    font = get_font(meeting.language)
    story = []

    # Title
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
        fontName=font,
    )
    story.append(Paragraph("Meeting Notes", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4a90d9")))
    story.append(Spacer(1, 0.3*cm))

    # Metadata
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=4,
        fontName=font,
    )
    story.append(Paragraph(f"<b>Date:</b> {meeting.created_at.strftime('%B %d, %Y %H:%M')}", meta_style))
    story.append(Paragraph(f"<b>Language:</b> {'Amharic' if meeting.language == 'am' else 'English'}", meta_style))
    story.append(Paragraph(f"<b>Source:</b> {meeting.source.replace('_', ' ').title()}", meta_style))
    story.append(Spacer(1, 0.5*cm))

    # Summary section
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#4a90d9"),
        spaceBefore=10,
        spaceAfter=6,
        fontName=font,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=11,
        leading=18,
        spaceAfter=4,
        fontName=font,
    )

    story.append(Paragraph("Summary", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))

    # Split summary into lines and add each as paragraph
    for line in meeting.summary.split("\n"):
        if line.strip():
            clean = line.replace("•", "&#8226;")
            story.append(Paragraph(clean, body_style))

    # Transcription section (if available)
    if meeting.transcription:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("Full Transcription", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.2*cm))

        transcription_style = ParagraphStyle(
            "Transcription",
            parent=styles["Normal"],
            fontSize=10,
            leading=16,
            textColor=colors.HexColor("#444444"),
            fontName=font,
        )
        story.append(Paragraph(meeting.transcription, transcription_style))

    doc.build(story)
    return pdf_path