from typing import TypedDict, List, Optional

from models import (
    StudentProfile,
    Scholarship,
    EligibilityResult,
    EvidenceRecord,
    ApplicationPlan
)


class ScholarshipState(TypedDict, total=False):

    # Input
    cv_path: str
    transcript_path: str
    ielts_path: Optional[str]
    country: str
    degree_level: str

    # Agent outputs
    student_profile: StudentProfile
    scholarships: List[Scholarship]
    eligibility_results: List[EligibilityResult]
    evidence_records: List[EvidenceRecord]
    application_plans: List[ApplicationPlan]
    shortlist: List[ApplicationPlan]

    # Workflow information
    current_agent: str
    messages: List[str]
    verification_attempts: int
    error: Optional[str]