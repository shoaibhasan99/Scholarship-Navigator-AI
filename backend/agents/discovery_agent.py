import json
import os
import re
from datetime import datetime
from typing import List
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient

from models import (
    StudentProfile,
    Scholarship,
    ScholarshipRequirement,
)


load_dotenv()


# ==========================================================
# CONFIG
# ==========================================================

USE_LIVE_DISCOVERY = (
    os.getenv("USE_LIVE_DISCOVERY", "true").lower() == "true"
)

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "scholarships.json",
)


# Country-specific discovery configuration.
# official_suffixes are mainly university/government domain suffixes.
# official_hosts are important national scholarship/study portals.
COUNTRY_CONFIG = {
    "South Korea": {
        "official_suffixes": [".ac.kr", ".go.kr"],
        "official_hosts": [
            "studyinkorea.go.kr",
        ],
        "keywords": [
            "GKS graduate scholarship",
            "international graduate scholarship",
            "graduate admission scholarship",
        ],
        "priority_terms": [
            "gks",
            "global korea scholarship",
            "studyinkorea",
        ],
    },

    "China": {
        "official_suffixes": [".edu.cn", ".gov.cn"],
        "official_hosts": [
            "campuschina.org",
            "csc.edu.cn",
        ],
        "keywords": [
            "Chinese Government Scholarship",
            "CSC scholarship",
            "international graduate scholarship",
        ],
        "priority_terms": [
            "chinese government scholarship",
            "csc scholarship",
            "campuschina",
        ],
    },

    "Japan": {
        "official_suffixes": [".ac.jp", ".go.jp"],
        "official_hosts": [
            "studyinjapan.go.jp",
            "mext.go.jp",
        ],
        "keywords": [
            "MEXT scholarship",
            "international graduate scholarship",
            "graduate admission scholarship",
        ],
        "priority_terms": [
            "mext",
            "study in japan",
        ],
    },

    "Taiwan": {
        "official_suffixes": [".edu.tw", ".gov.tw"],
        "official_hosts": [
            "studyintaiwan.org",
        ],
        "keywords": [
            "Taiwan Scholarship",
            "international graduate scholarship",
            "university graduate scholarship",
        ],
        "priority_terms": [
            "taiwan scholarship",
            "study in taiwan",
        ],
    },

    "Germany": {
        # German university domains are not standardized under one
        # university-only suffix, so .de is accepted and then filtered
        # by the relevance/quality checks below.
        "official_suffixes": [".de"],
        "official_hosts": [
            "daad.de",
            "study-in-germany.de",
        ],
        "keywords": [
            "DAAD scholarship",
            "international Masters scholarship",
            "graduate funding international students",
        ],
        "priority_terms": [
            "daad",
            "study in germany",
        ],
    },

    "Malaysia": {
        "official_suffixes": [".edu.my", ".gov.my"],
        "official_hosts": [],
        "keywords": [
            "international graduate scholarship",
            "Masters scholarship international students",
            "university graduate funding",
        ],
        "priority_terms": [
            "scholarship",
            "international students",
        ],
    },

    "Singapore": {
        "official_suffixes": [".edu.sg", ".gov.sg"],
        "official_hosts": [],
        "keywords": [
            "graduate scholarship international students",
            "Masters scholarship",
            "graduate funding international students",
        ],
        "priority_terms": [
            "scholarship",
            "graduate funding",
        ],
    },

    "Hong Kong": {
        "official_suffixes": [".edu.hk", ".gov.hk"],
        "official_hosts": [],
        "keywords": [
            "postgraduate scholarship international students",
            "Masters scholarship",
            "graduate funding international students",
        ],
        "priority_terms": [
            "scholarship",
            "postgraduate",
        ],
    },
}


# ==========================================================
# DEMO FALLBACK
# ==========================================================

def load_demo_scholarships() -> List[Scholarship]:
    with open(
        DATA_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        raw_data = json.load(file)

    return [
        Scholarship(**item)
        for item in raw_data
    ]


# ==========================================================
# OFFICIAL SOURCE FILTER
# ==========================================================

def _host_matches(host: str, rule: str) -> bool:
    rule = rule.lower().strip()
    host = host.lower().strip()

    return (
        host == rule
        or host.endswith("." + rule)
    )


def is_official_source(
    url: str,
    country: str,
) -> bool:
    """
    Accept official university/government/national-study sources
    for the selected country.
    """

    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False

    if not host:
        return False

    config = COUNTRY_CONFIG.get(country)

    if not config:
        return False

    for official_host in config["official_hosts"]:
        if _host_matches(host, official_host):
            return True

    for suffix in config["official_suffixes"]:
        if host.endswith(suffix):
            return True

    return False


# ==========================================================
# CANDIDATE RELEVANCE GUARD
# ==========================================================

def candidate_is_relevant(
    title: str,
    content: str,
    url: str,
    country: str,
) -> bool:
    """
    Reject clearly mismatched pages while keeping genuine
    scholarship/admission/funding opportunities.
    """

    title = (title or "").lower()
    content = (content or "").lower()
    url = (url or "").lower()

    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
    except Exception:
        return False

    combined = " ".join(
        [title, content, host, path]
    )

    # Reject clearly unrelated specialist faculties.
    bad_host_prefixes = [
        "law.",
        "dental.",
        "dentistry.",
        "medicine.",
        "medical.",
        "business.",
    ]

    if any(
        host.startswith(prefix)
        for prefix in bad_host_prefixes
    ):
        return False

    bad_path_terms = [
        "/law/",
        "/law.",
        "/dentistry/",
        "/dental/",
        "/medical-school/",
        "/business-school/",
    ]

    if any(
        term in path
        for term in bad_path_terms
    ):
        return False

    opportunity_terms = [
        "scholarship",
        "admission",
        "graduate",
        "postgraduate",
        "application",
        "funding",
        "fellowship",
        "tuition",
        "stipend",
        "international student",
        "international students",
        "masters",
        "master's",
        "phd",
        "gks",
        "global korea scholarship",
        "mext",
        "chinese government scholarship",
        "csc scholarship",
        "taiwan scholarship",
        "daad",
    ]

    if not any(
        term in combined
        for term in opportunity_terms
    ):
        return False

    # Reject generic root pages unless the title/content itself
    # clearly talks about admissions/scholarships/funding.
    normalized_path = path.rstrip("/")

    if normalized_path == "":
        strong_root_terms = [
            "scholarship",
            "admission",
            "funding",
            "graduate",
            "postgraduate",
        ]

        if not any(
            term in (title + " " + content)
            for term in strong_root_terms
        ):
            return False

    # Strong scholarship/admission pages are useful even when
    # the page is not explicitly AI-specific.
    strong_opportunity_terms = [
        "graduate scholarship",
        "postgraduate scholarship",
        "international scholarship",
        "scholarships - graduate",
        "graduate admissions",
        "graduate admission",
        "international graduate",
        "application guide",
        "admission guide",
        "government scholarship",
        "mext scholarship",
        "csc scholarship",
        "daad scholarship",
        "taiwan scholarship",
        "global korea scholarship",
    ]

    if any(
        term in combined
        for term in strong_opportunity_terms
    ):
        return True

    academic_terms = [
        "artificial intelligence",
        "computer science",
        "machine learning",
        "data science",
        "information technology",
        "electrical engineering",
        "computer engineering",
        "engineering",
        "graduate school",
        "school of computing",
        "department of computing",
        "informatics",
    ]

    academic_match = any(
        term in combined
        for term in academic_terms
    )

    # Central scholarship portals can be relevant even when
    # their search snippets do not mention AI/CS.
    config = COUNTRY_CONFIG.get(country, {})
    central_source = any(
        _host_matches(host, official_host)
        for official_host in config.get("official_hosts", [])
    )

    return academic_match or central_source


# ==========================================================
# HELPERS
# ==========================================================

def normalize_title(title: str) -> str:
    title = (title or "").lower()
    title = re.sub(r"\s+", " ", title)
    title = re.sub(r"[^a-z0-9 ]", "", title)
    return title.strip()


def is_generic_homepage(
    title: str,
    url: str,
) -> bool:
    title_lower = (title or "").strip().lower()

    try:
        parsed = urlparse(url or "")
        path = (parsed.path or "").strip().lower()
    except Exception:
        path = ""

    normalized_path = path.rstrip("/")

    if normalized_path != "":
        return False

    useful_terms = [
        "scholarship",
        "admission",
        "graduate",
        "postgraduate",
        "funding",
        "international",
    ]

    return not any(
        term in title_lower
        for term in useful_terms
    )


def is_central_or_government_source(
    url: str,
    country: str,
) -> bool:
    try:
        host = urlparse(url or "").netloc.lower()
    except Exception:
        return False

    config = COUNTRY_CONFIG.get(country, {})

    if any(
        _host_matches(host, official_host)
        for official_host in config.get("official_hosts", [])
    ):
        return True

    government_suffixes = [
        ".go.kr",
        ".gov.cn",
        ".go.jp",
        ".gov.tw",
        ".gov.my",
        ".gov.sg",
        ".gov.hk",
    ]

    return any(
        host.endswith(suffix)
        for suffix in government_suffixes
    )


# ==========================================================
# LIVE SEARCH
# ==========================================================

def live_discovery(
    profile: StudentProfile,
    country: str,
    degree_level: str,
) -> List[Scholarship]:

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is missing."
        )

    if country not in COUNTRY_CONFIG:
        raise ValueError(
            f"Unsupported country: {country}"
        )

    client = TavilyClient(
        api_key=api_key
    )

    field = (
        profile.academic.field_of_study
        or "Artificial Intelligence Computer Science"
    )

    interests = " ".join(
        profile.research_interests[:2]
    )

    current_year = datetime.now().year
    next_year = current_year + 1

    config = COUNTRY_CONFIG[country]

    # ======================================================
    # MULTIPLE TARGETED SEARCHES
    # ======================================================

    queries = []

    for keyword in config["keywords"]:
        queries.append(
            f"{country} {keyword} "
            f"{degree_level} {field} "
            f"international students "
            f"{current_year} {next_year}"
        )

    # Add one research-interest query when available.
    if interests:
        queries.append(
            f"{country} graduate scholarship "
            f"{degree_level} {field} "
            f"{interests} international students "
            f"{current_year} {next_year}"
        )

    # Keep discovery fast enough for the hackathon.
    queries = queries[:4]

    # ======================================================
    # SEARCH
    # ======================================================

    all_results = []
    seen_urls = set()

    print(
        f"\n🌐 Starting scholarship discovery for {country}..."
    )

    for index, query in enumerate(
        queries,
        start=1,
    ):
        print(
            f"\n🔎 Search {index}/{len(queries)}"
        )
        print(
            f"   {query[:120]}..."
        )

        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=6,
            )
        except Exception as error:
            print(
                f"⚠️ Search failed: {error}"
            )
            continue

        for result in response.get(
            "results",
            [],
        ):
            url = (
                result.get("url")
                or ""
            ).strip()

            if not url:
                continue

            if url in seen_urls:
                continue

            if not is_official_source(
                url,
                country,
            ):
                print(
                    f"⏭️ Non-official source skipped: {url}"
                )
                continue

            seen_urls.add(url)
            all_results.append(result)

    print(
        f"\n📥 Found {len(all_results)} unique "
        f"official-source pages for {country}."
    )

    # ======================================================
    # QUALITY FILTER
    # ======================================================

    quality_keywords = [
        "scholarship",
        "graduate",
        "postgraduate",
        "admission",
        "application",
        "international",
        "funding",
        "tuition",
        "stipend",
        "fellowship",
        "application guide",
        "master's",
        "masters",
        "ms/phd",
        "phd",
    ]

    academic_keywords = [
        "artificial intelligence",
        "computer science",
        "machine learning",
        "data science",
        "information technology",
        "engineering",
        "graduate school",
        "school of computing",
        "informatics",
    ]

    candidates = []

    for result in all_results:
        title = (
            result.get("title", "")
            or ""
        )

        content = (
            result.get("content", "")
            or ""
        )

        url = (
            result.get("url", "")
            or ""
        )

        if not candidate_is_relevant(
            title,
            content,
            url,
            country,
        ):
            print(
                f"🚫 Candidate rejected: {title[:70]}"
            )
            continue

        combined = (
            title
            + " "
            + content
            + " "
            + url
        ).lower()

        quality_score = 0

        # Scholarship/admission relevance.
        for keyword in quality_keywords:
            if keyword in combined:
                quality_score += 1

        # Academic relevance.
        academic_match = any(
            keyword in combined
            for keyword in academic_keywords
        )

        if academic_match:
            quality_score += 2

        # PDF/application guides are valuable.
        if ".pdf" in url.lower():
            quality_score += 2

        # Central scholarship/government sources are valuable.
        if is_central_or_government_source(
            url,
            country,
        ):
            quality_score += 3

        # Country-specific scholarship signals.
        if any(
            term in combined
            for term in config["priority_terms"]
        ):
            quality_score += 2

        # Prefer current/upcoming-cycle information.
        if str(current_year) in combined:
            quality_score += 1

        if str(next_year) in combined:
            quality_score += 1

        # Penalize generic homepages.
        if is_generic_homepage(
            title,
            url,
        ):
            quality_score -= 3

        # Penalize news/press pages.
        news_terms = [
            "news center",
            "press release",
            "news article",
            "newsroom",
            "holds",
        ]

        if any(
            term in combined
            for term in news_terms
        ):
            quality_score -= 3

        print(
            f"📊 Score {quality_score}: "
            f"{title[:70]}"
        )

        if quality_score < 3:
            print(
                "   ⏭️ Low-quality candidate skipped."
            )
            continue

        candidates.append(
            (
                quality_score,
                result,
            )
        )

    # ======================================================
    # RANK + DEDUPLICATE RESULTS
    # ======================================================

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    deduplicated_candidates = []
    seen_titles = set()

    for score, result in candidates:
        title_key = normalize_title(
            result.get("title", "")
        )

        if not title_key:
            title_key = (
                result.get("url", "")
                or ""
            ).lower()

        if title_key in seen_titles:
            continue

        seen_titles.add(title_key)

        deduplicated_candidates.append(
            (
                score,
                result,
            )
        )

    # ======================================================
    # BALANCED FINAL SELECTION
    # ======================================================
    # Keep up to 2 central/government opportunities and up to
    # 4 university opportunities in the final six.

    selected_candidates = []

    central_count = 0
    university_count = 0

    for score, result in deduplicated_candidates:
        candidate_url = (
            result.get("url", "")
            or ""
        )

        is_central = (
            is_central_or_government_source(
                candidate_url,
                country,
            )
        )

        if is_central:
            if central_count >= 2:
                continue

            central_count += 1
        else:
            if university_count >= 4:
                continue

            university_count += 1

        selected_candidates.append(
            (
                score,
                result,
            )
        )

        if len(selected_candidates) >= 6:
            break

    # If the balanced pass produced fewer than six, fill the
    # remaining spaces with the next best unused candidates.
    if len(selected_candidates) < 6:
        selected_urls = {
            item[1].get("url", "")
            for item in selected_candidates
        }

        for score, result in deduplicated_candidates:
            result_url = result.get("url", "")

            if result_url in selected_urls:
                continue

            selected_candidates.append(
                (
                    score,
                    result,
                )
            )
            selected_urls.add(result_url)

            if len(selected_candidates) >= 6:
                break

    scholarships = []

    for score, result in selected_candidates:
        url = result.get("url")
        title = result.get("title")
        content = result.get(
            "content",
            "",
        )

        scholarship = Scholarship(
            scholarship_name=(
                title
                or "Graduate Scholarship Opportunity"
            ),
            university=None,
            country=country,
            program_name=None,
            degree_level=degree_level,
            deadline=None,
            funding_details=None,
            official_url=url,
            source_title=title,
            source_snippet=content,
            requirements=ScholarshipRequirement(
                minimum_cgpa=None,
                cgpa_scale=None,
                required_degree=None,
                required_field=None,
                minimum_ielts=None,
                minimum_toefl=None,
                minimum_gre=None,
                english_waiver_possible=None,
            ),
            source_verified=False,
        )

        scholarships.append(
            scholarship
        )

    print(
        f"\n✅ Discovery Agent selected "
        f"{len(scholarships)} high-quality "
        f"{country} candidates."
    )

    return scholarships


# ==========================================================
# MAIN DISCOVERY AGENT
# ==========================================================

def discover_scholarships(
    profile: StudentProfile,
    country: str = "South Korea",
    degree_level: str = "Masters",
) -> List[Scholarship]:

    print(
        "\n🔎 Discovery Agent started..."
    )

    print(
        f"🎯 Looking for {degree_level} "
        f"opportunities in {country}..."
    )

    # Live mode.
    if USE_LIVE_DISCOVERY:
        try:
            scholarships = live_discovery(
                profile,
                country,
                degree_level,
            )

            if scholarships:
                print(
                    f"✅ Live Discovery Agent found "
                    f"{len(scholarships)} "
                    f"official-source candidates."
                )
                return scholarships

            print(
                "⚠️ No official live results found."
            )

        except Exception as error:
            print(
                f"⚠️ Live discovery failed: {error}"
            )

    # Demo fallback.
    print(
        "↩️ Switching to demo fallback dataset."
    )

    all_scholarships = load_demo_scholarships()

    matches = []

    for scholarship in all_scholarships:
        country_match = (
            scholarship.country
            and scholarship.country.lower()
            == country.lower()
        )

        level_match = (
            scholarship.degree_level
            and scholarship.degree_level.lower()
            == degree_level.lower()
        )

        if country_match and level_match:
            matches.append(
                scholarship
            )

    print(
        f"✅ Demo fallback found "
        f"{len(matches)} candidates."
    )

    return matches


# ==========================================================
# MANUAL TEST
# ==========================================================

if __name__ == "__main__":
    from agents.profile_agent import (
        build_profile,
    )

    profile = build_profile(
        "../uploads/CV.pdf",
        "../uploads/Transcript.pdf",
    )

    scholarships = discover_scholarships(
        profile=profile,
        country="Japan",
        degree_level="Masters",
    )

    print(
        "\n===== DISCOVERY RESULTS =====\n"
    )

    for index, scholarship in enumerate(
        scholarships,
        start=1,
    ):
        print(
            f"{index}. "
            f"{scholarship.scholarship_name}"
        )

        print(
            f"   Country: "
            f"{scholarship.country}"
        )

        print(
            f"   URL: "
            f"{scholarship.official_url}"
        )

        print()
