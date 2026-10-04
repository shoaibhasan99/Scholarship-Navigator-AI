from typing import List



from models import (

    StudentProfile,

    Scholarship,

    EligibilityResult,

    ApplicationPlan

)





# --------------------------------------------------

# Find scholarship by name

# --------------------------------------------------



def find_scholarship(

    scholarships: List[Scholarship],

    scholarship_name: str

):



    for scholarship in scholarships:



        if scholarship.scholarship_name == scholarship_name:

            return scholarship



    return None





# --------------------------------------------------

# Build required document list

# --------------------------------------------------



def get_required_documents(

    profile: StudentProfile,

    scholarship: Scholarship

) -> List[str]:



    documents = [

        "CV / Resume",

        "Academic Transcript",

        "Statement of Purpose",

        "Recommendation Letters"

    ]



    # IELTS

    if scholarship.requirements.minimum_ielts is not None:

        documents.append(

            "IELTS Score Report"

        )



    # GRE

    if scholarship.requirements.minimum_gre is not None:

        documents.append(

            "GRE Score Report"

        )



    return documents





# --------------------------------------------------

# Detect missing documents

# --------------------------------------------------



def get_missing_documents(

    profile: StudentProfile,

    scholarship: Scholarship

) -> List[str]:



    missing = []



    # CV

    if not profile.documents.cv_uploaded:

        missing.append(

            "CV / Resume"

        )



    # Transcript

    if not profile.documents.transcript_uploaded:

        missing.append(

            "Academic Transcript"

        )



    # IELTS

    if (

        scholarship.requirements.minimum_ielts

        is not None

    ):



        if (

            not profile.documents

            .ielts_certificate_uploaded

        ):

            missing.append(

                "IELTS Score Report"

            )



    # GRE

    if (

        scholarship.requirements.minimum_gre

        is not None

    ):



        if profile.gre_score is None:

            missing.append(

                "GRE Score Report"

            )



    return missing





# --------------------------------------------------

# Create next steps

# --------------------------------------------------



def create_next_steps(

    profile: StudentProfile,

    scholarship: Scholarship,

    result: EligibilityResult

) -> List[str]:



    steps = []



    # --------------------------------

    # Not eligible

    # --------------------------------



    if result.overall_status == "not_eligible":



        failed_requirements = [

            check.requirement

            for check in result.checks

            if check.status == "not_eligible"

        ]



        steps.append(

            "This scholarship is not currently "

            "recommended for the shortlist."

        )



        if failed_requirements:



            steps.append(

                "Eligibility issue: "

                + ", ".join(

                    failed_requirements

                )

            )



        return steps



    # --------------------------------

    # Verification required

    # --------------------------------



    if result.verification_needed:



        for requirement in result.verification_needed:



            if requirement == "IELTS":



                steps.append(

                    "Upload or verify the official "

                    "IELTS score report."

                )



            elif requirement == "Field of Study":



                steps.append(

                    "Confirm field-of-study eligibility "

                    "from the official program page."

                )



            else:



                steps.append(

                    f"Verify requirement: {requirement}."

                )



    # --------------------------------

    # Missing information

    # --------------------------------



    if result.missing_information:



        for item in result.missing_information:



            steps.append(

                f"Provide missing information: {item}."

            )



    # --------------------------------

    # General application steps

    # --------------------------------



    steps.extend(

        [

            "Review the official scholarship "

            "and program requirements.",



            "Prepare a tailored Statement of Purpose.",



            "Arrange recommendation letters.",



            "Check the application deadline "

            "and submission portal.",



            "Complete a final document review "

            "before submission."

        ]

    )



    return steps





# --------------------------------------------------

# Create one application plan

# --------------------------------------------------



def create_application_plan(

    profile: StudentProfile,

    scholarship: Scholarship,

    result: EligibilityResult

) -> ApplicationPlan:



    required_documents = get_required_documents(

        profile,

        scholarship

    )



    missing_documents = get_missing_documents(

        profile,

        scholarship

    )



    next_steps = create_next_steps(

        profile,

        scholarship,

        result

    )



    if result.overall_status == "not_eligible":



        notes = (

            "Not shortlisted because at least one "

            "mandatory eligibility requirement "

            "was not satisfied."

        )



    elif result.overall_status == "verification_required":



        notes = (

            "Potential match. One or more requirements "

            "still need verification."

        )



    elif result.overall_status == "missing_information":



        notes = (

            "Potential match, but more student "

            "information is required."

        )



    else:



        notes = (

            "Current profile satisfies the configured "

            "eligibility checks."

        )



    return ApplicationPlan(

        scholarship_name=scholarship.scholarship_name,

        status=result.overall_status,

        required_documents=required_documents,

        missing_documents=missing_documents,

        next_steps=next_steps,

        deadline=scholarship.deadline,

        notes=notes

    )





# --------------------------------------------------

# Planner Agent

# --------------------------------------------------



def generate_application_plans(

    profile: StudentProfile,

    scholarships: List[Scholarship],

    eligibility_results: List[EligibilityResult]

) -> List[ApplicationPlan]:



    print("\n📋 Application Planner Agent started...")



    plans = []



    for result in eligibility_results:



        scholarship = find_scholarship(

            scholarships,

            result.scholarship_name

        )



        if scholarship is None:



            print(

                f"⚠️ Scholarship not found: "

                f"{result.scholarship_name}"

            )



            continue



        plan = create_application_plan(

            profile,

            scholarship,

            result

        )



        plans.append(plan)



    print(

        f"✅ Planner Agent generated "

        f"{len(plans)} application plans."

    )



    return plans





# --------------------------------------------------

# Shortlist helper

# --------------------------------------------------



def get_shortlist(
    plans: List[ApplicationPlan],
    eligibility_results: List[EligibilityResult],
) -> List[ApplicationPlan]:
    """
    Return only defensible recommendations.

    A scholarship is shortlisted when:
    - it has no explicitly failed mandatory eligibility check, and
    - at least one eligibility requirement has been positively established.

    Opportunities with only unknown/verification-required checks remain in the
    full application plans, but they are not automatically presented as
    recommendations.
    """

    result_map = {
        result.scholarship_name: result
        for result in eligibility_results
    }

    shortlisted = []

    for plan in plans:
        result = result_map.get(
            plan.scholarship_name
        )

        if result is None:
            continue

        # Never recommend a scholarship with a failed mandatory requirement.
        failed_checks = [
            check
            for check in result.checks
            if check.status == "not_eligible"
        ]

        if failed_checks:
            continue

        # Require at least one positively established requirement.
        eligible_checks = [
            check
            for check in result.checks
            if check.status == "eligible"
        ]

        if eligible_checks:
            shortlisted.append(
                plan
            )

    return shortlisted





# --------------------------------------------------

# Manual test

# --------------------------------------------------



if __name__ == "__main__":

    from agents.profile_agent import build_profile

    from agents.discovery_agent import (
        discover_scholarships
    )

    from agents.eligibility_agent import (
        evaluate_all_scholarships
    )

    from agents.scholarship_verifier_agent import (
        verify_scholarship_sources
    )

    # --------------------------------------------------
    # 1. Profile Agent
    # --------------------------------------------------

    profile = build_profile(
        "../uploads/CV.pdf",
        "../uploads/Transcript.pdf"
    )

    # --------------------------------------------------
    # 2. Discovery Agent
    # --------------------------------------------------

    scholarships = discover_scholarships(
        profile,
        country="South Korea",
        degree_level="Masters"
    )

    # --------------------------------------------------
    # 3. Initial Eligibility Agent
    # --------------------------------------------------

    initial_results = evaluate_all_scholarships(
        profile,
        scholarships
    )

    # --------------------------------------------------
    # 4. Real Evidence Agent
    # --------------------------------------------------

    verified_scholarships, evidence_records = (
        verify_scholarship_sources(
            scholarships
        )
    )

    # --------------------------------------------------
    # 5. Re-run Eligibility using verified requirements
    # --------------------------------------------------

    updated_results = evaluate_all_scholarships(
        profile,
        verified_scholarships
    )

    # --------------------------------------------------
    # 6. Planner Agent
    # --------------------------------------------------

    plans = generate_application_plans(
        profile,
        verified_scholarships,
        updated_results
    )

    shortlist = get_shortlist(
        plans,
        updated_results
    )

    print(
        "\n===== APPLICATION PLANS =====\n"
    )

    for plan in plans:

        print(
            f"🎓 {plan.scholarship_name}"
        )

        print(
            f"Status: {plan.status}"
        )

        print(
            f"Deadline: {plan.deadline}"
        )

        print(
            f"Notes: {plan.notes}"
        )

        print(
            "\nRequired Documents:"
        )

        for document in plan.required_documents:
            print(
                f"  • {document}"
            )

        print(
            "\nMissing Documents:"
        )

        if plan.missing_documents:

            for document in plan.missing_documents:
                print(
                    f"  ⚠️ {document}"
                )

        else:
            print(
                "  ✅ No known missing documents."
            )

        print(
            "\nNext Steps:"
        )

        for step in plan.next_steps:
            print(
                f"  → {step}"
            )

        print(
            "\n"
            + "-" * 60
            + "\n"
        )

    print(
        "===== SHORTLIST =====\n"
    )

    if shortlist:

        for plan in shortlist:
            print(
                f"✅ {plan.scholarship_name}"
            )

    else:
        print(
            "⚠️ No scholarship currently has enough "
            "positive verified evidence for the shortlist."
        )

    print(
        f"\nEvidence records collected: "
        f"{len(evidence_records)}"
    )

