from typing import List

from models import (
    StudentProfile,
    Scholarship,
    EligibilityResult,
    EligibilityCheck
)


# --------------------------------------------------
# Helper: Degree check
# --------------------------------------------------

def check_degree(
    profile: StudentProfile,
    scholarship: Scholarship
) -> EligibilityCheck:

    student_degree = profile.academic.degree
    required_degree = scholarship.requirements.required_degree

    if not required_degree:
        return EligibilityCheck(
            requirement="Degree",
            student_value=student_degree,
            required_value=None,
            status="verification_required",
            explanation=(
                "Required degree could not be verified "
                "from the available official source."
            )
        )

    if not student_degree:
        return EligibilityCheck(
            requirement="Degree",
            student_value=None,
            required_value=required_degree,
            status="missing_information",
            explanation="Student degree information is missing."
        )

    # For MVP:
    # Bachelor requirement is satisfied by any Bachelor/BS degree.
    if (
        "bachelor" in required_degree.lower()
        and (
            "bachelor" in student_degree.lower()
            or student_degree.lower().startswith("bs")
        )
    ):
        return EligibilityCheck(
            requirement="Degree",
            student_value=student_degree,
            required_value=required_degree,
            status="eligible",
            explanation="Student holds the required bachelor-level degree."
        )

    return EligibilityCheck(
        requirement="Degree",
        student_value=student_degree,
        required_value=required_degree,
        status="verification_required",
        explanation="Degree equivalence requires verification."
    )


# --------------------------------------------------
# Helper: Field check
# --------------------------------------------------

def check_field(
    profile: StudentProfile,
    scholarship: Scholarship
) -> EligibilityCheck:

    student_field = profile.academic.field_of_study
    required_field = scholarship.requirements.required_field

    if not required_field:
        return EligibilityCheck(
            requirement="Field of Study",
            student_value=student_field,
            required_value=None,
            status="verification_required",
            explanation=(
                "Accepted field of study could not be "
                "verified from the available official source."
            )
        )

    if not student_field:
        return EligibilityCheck(
            requirement="Field of Study",
            student_value=None,
            required_value=required_field,
            status="missing_information",
            explanation="Student field of study is missing."
        )

    student_lower = student_field.lower()
    required_lower = required_field.lower()

    # Simple keyword matching for MVP
    ai_keywords = [
        "artificial intelligence",
        "ai"
    ]

    match = False

    for keyword in ai_keywords:
        if (
            keyword in student_lower
            and keyword in required_lower
        ):
            match = True
            break

    if match:
        return EligibilityCheck(
            requirement="Field of Study",
            student_value=student_field,
            required_value=required_field,
            status="eligible",
            explanation="Student field matches the scholarship requirement."
        )

    # Related-field wording should be verified,
    # not guessed.
    if "related" in required_lower:
        return EligibilityCheck(
            requirement="Field of Study",
            student_value=student_field,
            required_value=required_field,
            status="verification_required",
            explanation=(
                "Scholarship accepts related fields. "
                "Official verification is recommended."
            )
        )

    return EligibilityCheck(
        requirement="Field of Study",
        student_value=student_field,
        required_value=required_field,
        status="verification_required",
        explanation="Field compatibility requires verification."
    )


# --------------------------------------------------
# Helper: CGPA check
# --------------------------------------------------

def check_cgpa(
    profile: StudentProfile,
    scholarship: Scholarship
) -> EligibilityCheck:

    student_cgpa = profile.academic.cgpa
    student_scale = profile.academic.cgpa_scale

    minimum_cgpa = scholarship.requirements.minimum_cgpa
    required_scale = scholarship.requirements.cgpa_scale

    if minimum_cgpa is None:
        return EligibilityCheck(
            requirement="CGPA",
            student_value=(
                f"{student_cgpa}/{student_scale}"
                if student_cgpa is not None
                else None
            ),
            required_value=None,
            status="verification_required",
            explanation=(
                "Minimum CGPA requirement could not be "
                "verified from the available official source."
            )
        )

    if student_cgpa is None:
        return EligibilityCheck(
            requirement="CGPA",
            student_value=None,
            required_value=str(minimum_cgpa),
            status="missing_information",
            explanation="Student CGPA is missing."
        )

    # Do not compare different scales blindly.
    if (
        student_scale is not None
        and required_scale is not None
        and student_scale != required_scale
    ):
        return EligibilityCheck(
            requirement="CGPA",
            student_value=f"{student_cgpa}/{student_scale}",
            required_value=f"{minimum_cgpa}/{required_scale}",
            status="verification_required",
            explanation="CGPA scales differ and require conversion."
        )

    if student_cgpa >= minimum_cgpa:
        return EligibilityCheck(
            requirement="CGPA",
            student_value=f"{student_cgpa}/{student_scale}",
            required_value=f"{minimum_cgpa}/{required_scale}",
            status="eligible",
            explanation="Student meets the minimum CGPA requirement."
        )

    return EligibilityCheck(
        requirement="CGPA",
        student_value=f"{student_cgpa}/{student_scale}",
        required_value=f"{minimum_cgpa}/{required_scale}",
        status="not_eligible",
        explanation="Student does not meet the minimum CGPA requirement."
    )


# --------------------------------------------------
# Helper: IELTS check
# --------------------------------------------------

def check_ielts(
    profile: StudentProfile,
    scholarship: Scholarship
) -> EligibilityCheck:

    minimum_ielts = scholarship.requirements.minimum_ielts

    if minimum_ielts is None:
        return EligibilityCheck(
            requirement="IELTS",
            student_value=(
                str(profile.ielts.overall)
                if profile.ielts
                and profile.ielts.overall is not None
                else None
            ),
            required_value=None,
            status="verification_required",
            explanation=(
                "IELTS requirement could not be "
                "verified from the available official source."
            )
        )

    if not profile.ielts or profile.ielts.overall is None:
        return EligibilityCheck(
            requirement="IELTS",
            student_value=None,
            required_value=str(minimum_ielts),
            status="missing_information",
            explanation="IELTS score is missing."
        )

    student_score = profile.ielts.overall

    if student_score < minimum_ielts:
        return EligibilityCheck(
            requirement="IELTS",
            student_value=str(student_score),
            required_value=str(minimum_ielts),
            status="not_eligible",
            explanation=(
                "The stated IELTS score is below "
                "the minimum requirement."
            )
        )

    # Score meets requirement, but certificate
    # has not been independently verified.
    if not profile.ielts.verified:
        return EligibilityCheck(
            requirement="IELTS",
            student_value=str(student_score),
            required_value=str(minimum_ielts),
            status="verification_required",
            explanation=(
                "IELTS score meets the requirement, "
                "but supporting evidence has not been verified."
            )
        )

    return EligibilityCheck(
        requirement="IELTS",
        student_value=str(student_score),
        required_value=str(minimum_ielts),
        status="eligible",
        explanation="Verified IELTS score meets the requirement."
    )


# --------------------------------------------------
# Determine overall result
# --------------------------------------------------

def determine_overall_status(
    checks: List[EligibilityCheck]
) -> str:

    statuses = [
        check.status
        for check in checks
    ]

    if "not_eligible" in statuses:
        return "not_eligible"

    if "missing_information" in statuses:
        return "missing_information"

    if "verification_required" in statuses:
        return "verification_required"

    return "eligible"


# --------------------------------------------------
# Main Eligibility Agent
# --------------------------------------------------

def evaluate_scholarship(
    profile: StudentProfile,
    scholarship: Scholarship
) -> EligibilityResult:

    print(
        f"\n⚖️ Checking: "
        f"{scholarship.scholarship_name}"
    )

    checks = [
        check_degree(profile, scholarship),
        check_field(profile, scholarship),
        check_cgpa(profile, scholarship),
        check_ielts(profile, scholarship)
    ]

    overall_status = determine_overall_status(
        checks
    )

    missing_information = []
    verification_needed = []

    for check in checks:

        if check.status == "missing_information":
            missing_information.append(
                check.requirement
            )

        if check.status == "verification_required":
            verification_needed.append(
                check.requirement
            )

    return EligibilityResult(
        scholarship_name=scholarship.scholarship_name,
        overall_status=overall_status,
        checks=checks,
        missing_information=missing_information,
        verification_needed=verification_needed
    )


def evaluate_all_scholarships(
    profile: StudentProfile,
    scholarships: List[Scholarship]
) -> List[EligibilityResult]:

    print("\n⚖️ Eligibility Agent started...")

    results = []

    for scholarship in scholarships:

        result = evaluate_scholarship(
            profile,
            scholarship
        )

        results.append(result)

    print(
        f"\n✅ Eligibility Agent evaluated "
        f"{len(results)} scholarships."
    )

    return results


# --------------------------------------------------
# Manual test
# --------------------------------------------------

if __name__ == "__main__":

    from agents.profile_agent import build_profile
    from agents.discovery_agent import discover_scholarships

    profile = build_profile(
        "../uploads/CV.pdf",
        "../uploads/Transcript.pdf"
    )

    scholarships = discover_scholarships(
        profile=profile,
        country="South Korea",
        degree_level="Masters"
    )

    results = evaluate_all_scholarships(
        profile,
        scholarships
    )

    print("\n===== ELIGIBILITY RESULTS =====\n")

    for result in results:

        print(
            f"🎓 {result.scholarship_name}"
        )

        print(
            f"Overall Status: "
            f"{result.overall_status}"
        )

        for check in result.checks:

            print(
                f"  - {check.requirement}: "
                f"{check.status}"
            )

            print(
                f"    Student: "
                f"{check.student_value}"
            )

            print(
                f"    Required: "
                f"{check.required_value}"
            )

            print(
                f"    {check.explanation}"
            )

        if result.verification_needed:

            print(
                "  🔎 Verification needed:",
                ", ".join(
                    result.verification_needed
                )
            )

        print()