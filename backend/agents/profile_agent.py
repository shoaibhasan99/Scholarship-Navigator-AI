import os
import base64
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from models import StudentProfile
from tools.document_parser import process_document


load_dotenv()


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)


# Keep mock mode enabled for the hackathon fallback.
# When API credits are available, change this to False.
USE_MOCK_PROFILE = True


# ==========================================================
# IMAGE HELPER
# ==========================================================

def image_to_data_url(
    image_path: str
) -> str:
    """
    Convert a local PNG/JPG image into a base64 data URL
    so it can be sent to the multimodal model.
    """

    extension = os.path.splitext(
        image_path
    )[1].lower()

    if extension == ".png":

        mime_type = "image/png"

    elif extension in [
        ".jpg",
        ".jpeg"
    ]:

        mime_type = "image/jpeg"

    else:

        raise ValueError(
            f"Unsupported image format: {extension}"
        )

    with open(
        image_path,
        "rb"
    ) as image_file:

        encoded = base64.b64encode(
            image_file.read()
        ).decode(
            "utf-8"
        )

    return (
        f"data:{mime_type};base64,{encoded}"
    )


# ==========================================================
# ADD DOCUMENT CONTENT TO MULTIMODAL INPUT
# ==========================================================

def add_document_to_content(
    content: list,
    document_result: dict,
    heading: str,
    image_instruction: str
) -> None:
    """
    Add either extracted text or rendered document images
    to the multimodal request content.
    """

    if (
        document_result["document_type"]
        == "text"
    ):

        content.append(
            {
                "type": "input_text",
                "text": (
                    f"\n\n=== {heading} CONTENT ===\n"
                    + document_result["text"]
                )
            }
        )

        return

    content.append(
        {
            "type": "input_text",
            "text": (
                f"\n\n=== {heading} IMAGES ===\n"
                f"{image_instruction}"
            )
        }
    )

    for image_path in document_result[
        "images"
    ]:

        content.append(
            {
                "type": "input_image",
                "image_url":
                    image_to_data_url(
                        image_path
                    ),
                "detail": "high"
            }
        )


# ==========================================================
# PROFILE AGENT
# ==========================================================

def build_profile(
    cv_path: str,
    transcript_path: str,
    ielts_path: Optional[str] = None
) -> StudentProfile:

    print(
        "🧠 Profile Agent started..."
    )

    ielts_uploaded = bool(
        ielts_path
        and os.path.exists(
            ielts_path
        )
    )

    # ======================================================
    # MOCK / DEMO MODE
    # ======================================================

    if USE_MOCK_PROFILE:

        print(
            "⚠️ Mock mode enabled — skipping API call."
        )

        if ielts_uploaded:

            print(
                "📄 IELTS report detected — "
                "marking IELTS document as uploaded."
            )

        warnings = []

        if not ielts_uploaded:

            warnings.append(
                "IELTS score is stated in CV but "
                "not independently verified."
            )

        return StudentProfile(
            name="Shoaib Hasan",

            academic={
                "university":
                    "COMSATS University Islamabad",

                "degree":
                    "Bachelor of Science in "
                    "Artificial Intelligence",

                "field_of_study":
                    "Artificial Intelligence",

                "cgpa":
                    3.04,

                "cgpa_scale":
                    4.0,

                "graduation_year":
                    2026
            },

            ielts={
                "overall":
                    7.0,

                "listening":
                    7.5,

                "reading":
                    6.5,

                "writing":
                    7.0,

                "speaking":
                    6.5,

                "score_source":
                    (
                        "IELTS Report"
                        if ielts_uploaded
                        else "CV"
                    ),

                "verified":
                    ielts_uploaded
            },

            research_interests=[
                "Medical Image Analysis",
                "Computer Vision",
                "Generative AI",
                "Trustworthy AI",
                "Multimodal AI"
            ],

            technical_skills=[
                "Python",
                "PyTorch",
                "TensorFlow",
                "OpenCV",
                "FastAPI",
                "LangGraph"
            ],

            documents={
                "cv_uploaded":
                    True,

                "transcript_uploaded":
                    True,

                "ielts_certificate_uploaded":
                    ielts_uploaded,

                "gre_certificate_uploaded":
                    False
            },

            profile_confidence=(
                0.97
                if ielts_uploaded
                else 0.95
            ),

            missing_information=[
                "GRE score"
            ],

            warnings=warnings
        )

    # ======================================================
    # LIVE MODE
    # ======================================================

    # -------------------------
    # Process CV
    # -------------------------

    print(
        "📄 Reading CV..."
    )

    cv_result = process_document(
        cv_path
    )

    # -------------------------
    # Process Transcript
    # -------------------------

    print(
        "📄 Reading Transcript..."
    )

    transcript_result = process_document(
        transcript_path
    )

    # -------------------------
    # Process optional IELTS
    # -------------------------

    ielts_result = None

    if ielts_uploaded:

        print(
            "📄 Reading IELTS Report..."
        )

        ielts_result = process_document(
            ielts_path
        )

    else:

        print(
            "ℹ️ No IELTS report supplied."
        )

    content = []

    # -------------------------
    # Main instructions
    # -------------------------

    instruction_text = """
You are the Profile Agent for a scholarship
navigation system.

Your job is to extract a student's academic
profile only from the documents provided.

Extract:

- Student name
- University
- Degree
- Field of study
- CGPA
- CGPA scale
- Graduation year
- IELTS scores
- GRE score if available
- Research interests
- Technical skills
- Missing information
- Warnings

IMPORTANT RULES:

1. Never invent information.
2. If a value is unavailable, use null.
3. Distinguish stated information from verified
   documentary evidence.
4. An IELTS score written only on a CV is not
   independently verified.
5. If an IELTS score report is supplied, use that
   report as the primary source for IELTS scores.
6. Transcript information should take priority
   over CV information for CGPA and academic record.
7. If documents conflict, include a warning.
8. profile_confidence must be between 0 and 1.
9. Only use information visible in the supplied
   documents.
10. If an IELTS report is supplied and its score
    information is readable, set score_source to
    "IELTS Report".
"""

    content.append(
        {
            "type": "input_text",
            "text": instruction_text
        }
    )

    # -------------------------
    # Add CV
    # -------------------------

    add_document_to_content(
        content=content,
        document_result=cv_result,
        heading="CV",
        image_instruction=(
            "Read the CV carefully."
        )
    )

    # -------------------------
    # Add Transcript
    # -------------------------

    add_document_to_content(
        content=content,
        document_result=transcript_result,
        heading="TRANSCRIPT",
        image_instruction=(
            "Read the academic record carefully."
        )
    )

    # -------------------------
    # Add IELTS Report
    # -------------------------

    if ielts_result is not None:

        add_document_to_content(
            content=content,
            document_result=ielts_result,
            heading="IELTS REPORT",
            image_instruction=(
                "Read all IELTS band scores, "
                "overall score, candidate details, "
                "and test information carefully."
            )
        )

    # -------------------------
    # OpenAI structured output
    # -------------------------

    print(
        "🤖 Extracting structured profile..."
    )

    response = client.responses.parse(
        model=MODEL,

        input=[
            {
                "role": "user",
                "content": content
            }
        ],

        text_format=StudentProfile,

        store=False
    )

    profile = response.output_parsed

    if profile is None:

        raise RuntimeError(
            "Profile Agent could not parse "
            "the model response."
        )

    # ======================================================
    # DETERMINISTIC DOCUMENT FLAGS
    # ======================================================

    profile.documents.cv_uploaded = True

    profile.documents.transcript_uploaded = True

    profile.documents.ielts_certificate_uploaded = (
        ielts_uploaded
    )

    # If an actual IELTS report was supplied, the IELTS
    # values extracted from that document are treated as
    # document-backed. Otherwise CV-only IELTS is unverified.
    if profile.ielts:

        profile.ielts.verified = (
            ielts_uploaded
        )

        if ielts_uploaded:

            profile.ielts.score_source = (
                "IELTS Report"
            )

    # Remove the CV-only IELTS warning when a report exists.
    if ielts_uploaded:

        profile.warnings = [
            warning
            for warning in profile.warnings
            if (
                "IELTS score is stated in CV"
                not in warning
            )
        ]

    print(
        "✅ Profile Agent completed."
    )

    return profile


# ==========================================================
# MANUAL TEST
# ==========================================================

if __name__ == "__main__":

    cv_path = (
        "../uploads/CV.pdf"
    )

    transcript_path = (
        "../uploads/Transcript.pdf"
    )

    # Optional:
    # Replace None with a real PDF path to test IELTS upload.
    ielts_path = None

    profile = build_profile(
        cv_path,
        transcript_path,
        ielts_path
    )

    print(
        "\n===== STUDENT PROFILE =====\n"
    )

    print(
        profile.model_dump_json(
            indent=2
        )
    )
