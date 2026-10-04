import json
import os
from typing import List

from models import (
    EligibilityResult,
    EvidenceRecord
)

from agents.eligibility_agent import determine_overall_status


# ---------------------------------------------
# Evidence dataset path
# ---------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

EVIDENCE_PATH = os.path.join(
    BASE_DIR,
    "data",
    "evidence.json"
)


# ---------------------------------------------
# Load evidence cache
# ---------------------------------------------

def load_evidence() -> list:

    with open(
        EVIDENCE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ---------------------------------------------
# Find evidence
# ---------------------------------------------

def find_evidence(
    scholarship_name: str,
    requirement: str
):

    evidence_data = load_evidence()

    for item in evidence_data:

        if (
            item["scholarship_name"]
            == scholarship_name
            and
            item["requirement"].lower()
            == requirement.lower()
        ):
            return item

    return None


# ---------------------------------------------
# Verify one requirement
# ---------------------------------------------

def verify_requirement(
    scholarship_name: str,
    requirement: str
) -> EvidenceRecord:

    print(
        f"🔍 Evidence Agent checking "
        f"{requirement}..."
    )

    item = find_evidence(
        scholarship_name,
        requirement
    )

    # No evidence found
    if item is None:

        return EvidenceRecord(
            scholarship_name=scholarship_name,
            claim=requirement,
            source_url=None,
            source_type="none",
            verified=False,
            evidence_text=(
                "No supporting evidence was found."
            ),
            conflict_detected=False
        )

    return EvidenceRecord(
        scholarship_name=scholarship_name,
        claim=requirement,
        source_url=item.get("source_url"),
        source_type=item.get("source_type"),
        verified=item.get("verified", False),
        evidence_text=item.get("evidence_text"),
        conflict_detected=item.get(
            "conflict_detected",
            False
        )
    )


# ---------------------------------------------
# Verify one eligibility result
# ---------------------------------------------

def verify_eligibility_result(
    result: EligibilityResult
) -> List[EvidenceRecord]:

    evidence_records = []

    if not result.verification_needed:
        return evidence_records

    print(
        f"\n🔎 Verifying evidence for: "
        f"{result.scholarship_name}"
    )

    for requirement in result.verification_needed:

        record = verify_requirement(
            result.scholarship_name,
            requirement
        )

        evidence_records.append(record)

    return evidence_records


# ---------------------------------------------
# Apply verified evidence
# ---------------------------------------------

def apply_evidence(
    result: EligibilityResult,
    evidence_records: List[EvidenceRecord]
) -> EligibilityResult:

    for evidence in evidence_records:

        if not evidence.verified:
            continue

        # Find matching eligibility check
        for check in result.checks:

            if (
                check.requirement.lower()
                != evidence.claim.lower()
            ):
                continue

            # --------------------------------
            # Field of Study
            # --------------------------------

            if check.requirement == "Field of Study":

                check.status = "eligible"

                check.explanation = (
                    "Field compatibility was verified "
                    "by the Evidence Agent."
                )

            # --------------------------------
            # IELTS
            # --------------------------------

            elif check.requirement == "IELTS":

                # Important:
                # scholarship requirement may be verified,
                # but student IELTS document is still
                # unverified.

                check.status = "verification_required"

                check.explanation = (
                    "Scholarship IELTS requirement was "
                    "verified. Student score meets the "
                    "requirement, but IELTS supporting "
                    "document is still unverified."
                )

    # Rebuild verification-needed list
    result.verification_needed = [
        check.requirement
        for check in result.checks
        if check.status == "verification_required"
    ]

    result.missing_information = [
        check.requirement
        for check in result.checks
        if check.status == "missing_information"
    ]

    # Recalculate overall result
    result.overall_status = determine_overall_status(
        result.checks
    )

    return result


# ---------------------------------------------
# Main Evidence Agent
# ---------------------------------------------

def verify_all_results(
    results: List[EligibilityResult]
):

    print("\n🔍 Evidence Agent started...")

    print(
        "⚠️ Demo evidence mode: "
        "using local verification dataset."
    )

    all_evidence = []

    updated_results = []

    for result in results:

        records = verify_eligibility_result(
            result
        )

        all_evidence.extend(records)

        updated_result = apply_evidence(
            result,
            records
        )

        updated_results.append(
            updated_result
        )

    print(
        f"\n✅ Evidence Agent generated "
        f"{len(all_evidence)} evidence records."
    )

    return updated_results, all_evidence


# ---------------------------------------------
# Manual Test
# ---------------------------------------------

if __name__ == "__main__":

    from agents.profile_agent import build_profile

    from agents.discovery_agent import (
        discover_scholarships
    )

    from agents.eligibility_agent import (
        evaluate_all_scholarships
    )

    profile = build_profile(
        "../uploads/CV.pdf",
        "../uploads/Transcript.pdf"
    )

    scholarships = discover_scholarships(
        profile,
        country="South Korea",
        degree_level="Masters"
    )

    results = evaluate_all_scholarships(
        profile,
        scholarships
    )

    updated_results, evidence = verify_all_results(
        results
    )

    print(
        "\n===== EVIDENCE RESULTS =====\n"
    )

    for record in evidence:

        print(
            f"🎓 {record.scholarship_name}"
        )

        print(
            f"Claim: {record.claim}"
        )

        print(
            f"Verified: {record.verified}"
        )

        print(
            f"Source Type: "
            f"{record.source_type}"
        )

        print(
            f"Evidence: "
            f"{record.evidence_text}"
        )

        print()

    print(
        "\n===== UPDATED ELIGIBILITY =====\n"
    )

    for result in updated_results:

        print(
            f"🎓 {result.scholarship_name}"
        )

        print(
            f"Overall: "
            f"{result.overall_status}"
        )

        for check in result.checks:

            print(
                f"  {check.requirement}: "
                f"{check.status}"
            )

        print()