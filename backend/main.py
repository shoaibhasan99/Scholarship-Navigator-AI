import os
import shutil
import uuid

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

from graph import scholarship_graph


# ==========================================================
# PATHS
# ==========================================================

BACKEND_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.dirname(
    BACKEND_DIR
)

UPLOAD_DIR = os.path.join(
    PROJECT_ROOT,
    "uploads"
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ==========================================================
# FASTAPI APP
# ==========================================================

app = FastAPI(
    title="Scholarship Navigator AI",
    description=(
        "Agentic AI system for scholarship discovery, "
        "eligibility verification and application planning."
    ),
    version="1.0.0"
)


# ==========================================================
# CORS
# ==========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.get("/")
def root():

    return {
        "project": "Scholarship Navigator AI",
        "status": "running",
        "message": "Scholarship Dhundo, Future Banao 🎓"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ==========================================================
# SAVE FILE
# ==========================================================

def save_uploaded_file(
    uploaded_file: UploadFile,
    prefix: str
) -> str:

    if not uploaded_file.filename:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file has no filename."
        )

    extension = os.path.splitext(
        uploaded_file.filename
    )[1].lower()

    if extension != ".pdf":

        raise HTTPException(
            status_code=400,
            detail=(
                f"{prefix} must be a PDF file."
            )
        )

    unique_name = (
        f"{prefix}_"
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    destination = os.path.join(
        UPLOAD_DIR,
        unique_name
    )

    with open(
        destination,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            uploaded_file.file,
            buffer
        )

    return destination


# ==========================================================
# MAIN ANALYSIS ENDPOINT
# ==========================================================

@app.post("/analyze")
def analyze_student(
    cv: UploadFile = File(...),

    transcript: UploadFile = File(...),

    ielts: UploadFile | None = File(None),

    country: str = Form("South Korea"),

    degree_level: str = Form("Masters")
):

    cv_path = None
    transcript_path = None
    ielts_path = None

    try:

        print("\n" + "=" * 70)
        print("🚀 NEW SCHOLARSHIP ANALYSIS REQUEST")
        print("=" * 70)

        # -----------------------------------------
        # Save required uploaded documents
        # -----------------------------------------

        cv_path = save_uploaded_file(
            cv,
            "cv"
        )

        transcript_path = save_uploaded_file(
            transcript,
            "transcript"
        )

        print(
            f"📄 CV saved: {cv_path}"
        )

        print(
            f"📄 Transcript saved: "
            f"{transcript_path}"
        )

        # -----------------------------------------
        # Save optional IELTS report
        # -----------------------------------------

        if ielts is not None and ielts.filename:

            ielts_path = save_uploaded_file(
                ielts,
                "ielts"
            )

            print(
                f"📄 IELTS report saved: "
                f"{ielts_path}"
            )

        else:

            print(
                "ℹ️ No IELTS report uploaded."
            )

        # -----------------------------------------
        # Create initial LangGraph state
        # -----------------------------------------

        initial_state = {

            "cv_path":
                cv_path,

            "transcript_path":
                transcript_path,

            "ielts_path":
                ielts_path,

            "country":
                country,

            "degree_level":
                degree_level,

            "verification_attempts":
                0,

            "messages":
                []
        }

        # -----------------------------------------
        # Run Agentic AI workflow
        # -----------------------------------------

        final_state = (
            scholarship_graph.invoke(
                initial_state
            )
        )

        # -----------------------------------------
        # Check workflow error
        # -----------------------------------------

        if final_state.get("error"):

            raise HTTPException(
                status_code=500,
                detail=final_state["error"]
            )

        # -----------------------------------------
        # API response
        # -----------------------------------------

        response = {

            "success": True,

            "student_profile":
                final_state.get(
                    "student_profile"
                ),

            "scholarships":
                final_state.get(
                    "scholarships",
                    []
                ),

            "eligibility_results":
                final_state.get(
                    "eligibility_results",
                    []
                ),

            "evidence_records":
                final_state.get(
                    "evidence_records",
                    []
                ),

            "application_plans":
                final_state.get(
                    "application_plans",
                    []
                ),

            "shortlist":
                final_state.get(
                    "shortlist",
                    []
                ),

            "agent_activity":
                final_state.get(
                    "messages",
                    []
                )
        }

        return jsonable_encoder(
            response
        )

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"❌ API Error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
