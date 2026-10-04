from models import (
    StudentProfile,
    AcademicProfile,
    IELTSScore,
    DocumentStatus
)


profile = StudentProfile(
    name="Shoaib Hasan",

    academic=AcademicProfile(
        university="COMSATS University Islamabad",
        degree="Bachelor of Science in Artificial Intelligence",
        field_of_study="Artificial Intelligence",
        cgpa=3.04,
        cgpa_scale=4.0,
        graduation_year=2026
    ),

    ielts=IELTSScore(
        overall=7.0,
        listening=7.5,
        reading=6.5,
        writing=7.0,
        speaking=6.5,
        score_source="CV",
        verified=False
    ),

    documents=DocumentStatus(
        cv_uploaded=True,
        transcript_uploaded=True,
        ielts_certificate_uploaded=False,
        gre_certificate_uploaded=False
    ),

    profile_confidence=0.95
)

print(profile.model_dump_json(indent=2))