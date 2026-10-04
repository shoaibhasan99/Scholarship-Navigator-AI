from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# -----------------------------
# IELTS
# -----------------------------

class IELTSScore(BaseModel):
    overall: Optional[float] = None
    listening: Optional[float] = None
    reading: Optional[float] = None
    writing: Optional[float] = None
    speaking: Optional[float] = None

    score_source: Optional[str] = None
    verified: bool = False


# -----------------------------
# Academic Profile
# -----------------------------

class AcademicProfile(BaseModel):
    university: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    cgpa: Optional[float] = None
    cgpa_scale: Optional[float] = 4.0
    graduation_year: Optional[int] = None


# -----------------------------
# Uploaded Documents
# -----------------------------

class DocumentStatus(BaseModel):
    cv_uploaded: bool = False
    transcript_uploaded: bool = False
    ielts_certificate_uploaded: bool = False
    gre_certificate_uploaded: bool = False


# -----------------------------
# Student Profile
# -----------------------------

class StudentProfile(BaseModel):
    name: Optional[str] = None
    academic: AcademicProfile
    ielts: Optional[IELTSScore] = None
    gre_score: Optional[float] = None

    research_interests: List[str] = []
    technical_skills: List[str] = []

    documents: DocumentStatus

    profile_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )

    missing_information: List[str] = []
    warnings: List[str] = []


# -----------------------------
# Scholarship Information
# -----------------------------

class ScholarshipRequirement(BaseModel):
    minimum_cgpa: Optional[float] = None
    cgpa_scale: Optional[float] = 4.0

    required_degree: Optional[str] = None
    required_field: Optional[str] = None

    # None = not stated / unknown
    # True = IELTS explicitly required
    # False = IELTS explicitly not required / waived
    ielts_required: Optional[bool] = None
    minimum_ielts: Optional[float] = None

    minimum_toefl: Optional[float] = None
    minimum_gre: Optional[float] = None

    english_waiver_possible: Optional[bool] = None


class Scholarship(BaseModel):
    scholarship_name: str

    university: Optional[str] = None
    country: Optional[str] = None
    program_name: Optional[str] = None
    degree_level: Optional[str] = None

    # Current / upcoming application cycle
    opening_date: Optional[str] = None
    deadline: Optional[str] = None

    # Previous cycle reference.
    # These fields must stay separate from current dates so the UI
    # does not accidentally present old dates as current deadlines.
    previous_cycle_year: Optional[int] = None
    previous_opening_date: Optional[str] = None
    previous_deadline: Optional[str] = None
    previous_cycle_source_url: Optional[str] = None

    funding_details: Optional[str] = None

    official_url: Optional[str] = None
    source_title: Optional[str] = None
    source_snippet: Optional[str] = None

    requirements: ScholarshipRequirement

    source_verified: bool = False

    verification_notes: List[str] = Field(
        default_factory=list
    )


# -----------------------------
# Eligibility Result
# -----------------------------

EligibilityStatus = Literal[
    "eligible",
    "potentially_eligible",
    "not_eligible",
    "missing_information",
    "verification_required"
]


class EligibilityCheck(BaseModel):
    requirement: str
    student_value: Optional[str] = None
    required_value: Optional[str] = None
    status: EligibilityStatus
    explanation: Optional[str] = None


class EligibilityResult(BaseModel):
    scholarship_name: str
    overall_status: EligibilityStatus
    checks: List[EligibilityCheck]
    missing_information: List[str] = []
    verification_needed: List[str] = []


# -----------------------------
# Evidence
# -----------------------------

class EvidenceRecord(BaseModel):
    scholarship_name: str
    claim: str
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    verified: bool = False
    evidence_text: Optional[str] = None
    conflict_detected: bool = False


# -----------------------------
# Application Plan
# -----------------------------

class ApplicationPlan(BaseModel):
    scholarship_name: str
    status: EligibilityStatus
    required_documents: List[str] = []
    missing_documents: List[str] = []
    next_steps: List[str] = []
    deadline: Optional[str] = None
    notes: Optional[str] = None
