import os
import re
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient
from tavily.errors import TimeoutError as TavilyTimeoutError

from models import (
    Scholarship,
    EvidenceRecord,
)


load_dotenv()


# ==========================================================
# CLIENT
# ==========================================================

def get_tavily_client():
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is missing.")

    return TavilyClient(api_key=api_key)


# ==========================================================
# TEXT HELPERS
# ==========================================================

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


MONTH_PATTERN = (
    r"(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
)

DATE_PATTERN = (
    rf"(?:"
    rf"{MONTH_PATTERN}\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,)?\s+20\d{{2}}"
    rf"|"
    rf"\d{{1,2}}(?:st|nd|rd|th)?\s+{MONTH_PATTERN}\s+20\d{{2}}"
    rf"|"
    rf"20\d{{2}}[-/.]\d{{1,2}}[-/.]\d{{1,2}}"
    rf"|"
    rf"\d{{1,2}}[-/.]\d{{1,2}}[-/.]20\d{{2}}"
    rf")"
)


def find_dates(text: str) -> List[str]:
    dates = []

    for match in re.finditer(
        DATE_PATTERN,
        text,
        flags=re.IGNORECASE,
    ):
        date = clean_text(match.group(0))

        if date not in dates:
            dates.append(date)

    return dates


# ==========================================================
# IELTS EXTRACTION
# ==========================================================

def extract_ielts(
    text: str,
) -> Tuple[Optional[float], Optional[str]]:
    patterns = [
        r"minimum\s+IELTS.{0,30}?([4-9](?:\.0|\.5)?)",
        r"IELTS.{0,30}?(?:minimum|at least|required|score of|overall)"
        r".{0,20}?([4-9](?:\.0|\.5)?)",
        r"IELTS\s*(?:Academic)?\s*[:\-]?\s*([4-9](?:\.0|\.5)?)",
        r"IELTS.{0,40}?([4-9](?:\.0|\.5)?)",
    ]

    scores = []

    for pattern in patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            try:
                value = float(match)

                if 4.0 <= value <= 9.0:
                    scores.append(value)

            except ValueError:
                pass

    unique_scores = sorted(set(scores))

    if len(unique_scores) == 1:
        return unique_scores[0], None

    if len(unique_scores) > 1:
        return (
            None,
            "Multiple IELTS values found in official source: "
            f"{unique_scores}",
        )

    return None, "IELTS minimum score not found."


def extract_ielts_required(
    text: str,
    minimum_ielts: Optional[float],
) -> Optional[bool]:
    """
    Returns:
      True  -> IELTS is explicitly required / a minimum IELTS score is stated.
      False -> IELTS is explicitly not required or explicitly waived.
      None  -> the official text is unclear.
    """

    lower = text.lower()

    negative_patterns = [
        r"ielts\s+(?:is\s+)?not\s+required",
        r"ielts\s+not\s+required",
        r"no\s+ielts\s+(?:is\s+)?required",
        r"ielts\s+(?:requirement\s+)?(?:is\s+)?waived",
        r"waiver.{0,40}ielts",
        r"english\s+(?:language\s+)?test\s+(?:is\s+)?not\s+required",
    ]

    if any(
        re.search(pattern, lower, flags=re.IGNORECASE)
        for pattern in negative_patterns
    ):
        return False

    if minimum_ielts is not None:
        return True

    positive_patterns = [
        r"ielts.{0,30}required",
        r"required.{0,30}ielts",
        r"minimum.{0,30}ielts",
        r"ielts.{0,30}minimum",
    ]

    if any(
        re.search(pattern, lower, flags=re.IGNORECASE)
        for pattern in positive_patterns
    ):
        return True

    return None


# ==========================================================
# TOEFL EXTRACTION
# ==========================================================

def extract_toefl(
    text: str,
) -> Tuple[Optional[float], Optional[str]]:
    patterns = [
        r"minimum\s+TOEFL(?:\s+iBT)?.{0,20}?(\d{2,3})",
        r"TOEFL(?:\s+iBT)?.{0,30}?(?:minimum|at least|required|score of)"
        r".{0,20}?(\d{2,3})",
        r"TOEFL(?:\s+iBT)?\s*[:\-]?\s*(\d{2,3})",
    ]

    scores = []

    for pattern in patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            try:
                value = float(match)

                # Common iBT range; this avoids years/page numbers.
                if 40 <= value <= 120:
                    scores.append(value)

            except ValueError:
                pass

    unique_scores = sorted(set(scores))

    if len(unique_scores) == 1:
        return unique_scores[0], None

    if len(unique_scores) > 1:
        return (
            None,
            "Multiple TOEFL values found in official source: "
            f"{unique_scores}",
        )

    return None, "TOEFL minimum score not found."


# ==========================================================
# GPA / CGPA EXTRACTION
# ==========================================================

def extract_cgpa(
    text: str,
) -> Tuple[
    Optional[float],
    Optional[float],
    Optional[str],
]:
    patterns = [
        (
            r"(?:minimum|required|at least)?"
            r".{0,20}?(?:CGPA|GPA)"
            r".{0,30}?"
            r"([0-5](?:\.\d{1,2})?)"
            r"\s*/\s*"
            r"([4-5](?:\.\d{1,2})?)"
        ),
        (
            r"(?:CGPA|GPA)"
            r".{0,30}?"
            r"([0-5](?:\.\d{1,2})?)"
            r"\s+(?:out of|on a scale of)\s+"
            r"([4-5](?:\.\d{1,2})?)"
        ),
    ]

    values = []

    for pattern in patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for score, scale in matches:
            try:
                score_value = float(score)
                scale_value = float(scale)

                if (
                    0 <= score_value <= scale_value
                    and 4.0 <= scale_value <= 5.0
                ):
                    values.append(
                        (
                            score_value,
                            scale_value,
                        )
                    )

            except ValueError:
                pass

    unique_values = list(set(values))

    if len(unique_values) == 1:
        score, scale = unique_values[0]
        return score, scale, None

    if len(unique_values) > 1:
        return (
            None,
            None,
            "Multiple GPA values found in official source: "
            f"{unique_values}",
        )

    return (
        None,
        None,
        "Minimum CGPA/GPA not found.",
    )


# ==========================================================
# DEGREE EXTRACTION
# ==========================================================

def extract_required_degree(
    text: str,
) -> Optional[str]:
    lower = text.lower()

    bachelor_patterns = [
        "bachelor's degree",
        "bachelor degree",
        "bachelor’s degree",
        "four-year bachelor's",
        "4-year bachelor's",
        "undergraduate degree",
        "first university degree",
    ]

    for phrase in bachelor_patterns:
        if phrase in lower:
            return "Bachelor"

    return None


# ==========================================================
# ENGLISH WAIVER
# ==========================================================

def extract_english_waiver(
    text: str,
) -> Optional[bool]:
    lower = text.lower()

    waiver_terms = [
        "english proficiency waiver",
        "english test waiver",
        "waiver of english",
        "medium of instruction",
        "english-medium institution",
        "degree taught in english",
        "previous degree was taught in english",
    ]

    for term in waiver_terms:
        if term in lower:
            return True

    return None


# ==========================================================
# APPLICATION DATES
# ==========================================================

def extract_application_dates(
    text: str,
) -> Tuple[
    Optional[str],
    Optional[str],
    Optional[str],
]:
    """
    Returns:
        opening_date, deadline, note

    The function only returns dates when they are near application
    timing language. It does not guess from unrelated dates on a page.
    """

    opening_date = None
    deadline = None
    notes = []

    # ------------------------------------------------------
    # 1. Strongest signal: an explicit application period
    #    containing two dates.
    # ------------------------------------------------------
    period_sections = re.findall(
        r".{0,60}"
        r"(?:application period|application window|submission period|"
        r"applications? (?:are )?open|applications? accepted)"
        r".{0,220}",
        text,
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    )

    for section in period_sections:
        dates = find_dates(section)

        if len(dates) >= 2:
            opening_date = dates[0]
            deadline = dates[1]
            break

    # ------------------------------------------------------
    # 2. Explicit opening/start language.
    # ------------------------------------------------------
    if opening_date is None:
        opening_sections = re.findall(
            r".{0,60}"
            r"(?:opening date|application opens?|applications open|"
            r"application starts?|application begins?|submission starts?)"
            r".{0,120}",
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        opening_dates = []

        for section in opening_sections:
            opening_dates.extend(
                find_dates(section)
            )

        opening_dates = list(
            dict.fromkeys(opening_dates)
        )

        if len(opening_dates) == 1:
            opening_date = opening_dates[0]

        elif len(opening_dates) > 1:
            notes.append(
                "Multiple possible opening dates found."
            )

    # ------------------------------------------------------
    # 3. Explicit deadline/closing language.
    # ------------------------------------------------------
    if deadline is None:
        deadline_sections = re.findall(
            r".{0,60}"
            r"(?:application deadline|submission deadline|deadline|"
            r"closing date|applications? close(?:s|d)?|apply by)"
            r".{0,120}",
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        deadline_dates = []

        for section in deadline_sections:
            deadline_dates.extend(
                find_dates(section)
            )

        deadline_dates = list(
            dict.fromkeys(deadline_dates)
        )

        if len(deadline_dates) == 1:
            deadline = deadline_dates[0]

        elif len(deadline_dates) > 1:
            notes.append(
                "Multiple possible application deadlines found."
            )

    if opening_date is None:
        notes.append(
            "Application opening date not confidently extracted."
        )

    if deadline is None:
        notes.append(
            "Application deadline not confidently extracted."
        )

    note = " ".join(notes) if notes else None

    return (
        opening_date,
        deadline,
        note,
    )


# ==========================================================
# FUNDING EXTRACTION
# ==========================================================

def extract_funding(
    text: str,
) -> Optional[str]:
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    keywords = [
        "fully funded",
        "full scholarship",
        "full tuition",
        "tuition exemption",
        "tuition waiver",
        "tuition fee",
        "monthly stipend",
        "monthly allowance",
        "living allowance",
        "living expenses",
        "airfare",
        "air ticket",
        "accommodation",
        "housing",
        "medical insurance",
        "health insurance",
        "scholarship covers",
        "research assistantship",
        "research grant",
    ]

    matches = []

    for sentence in sentences:
        lower = sentence.lower()

        if any(
            keyword in lower
            for keyword in keywords
        ):
            cleaned = sentence.strip()

            if (
                cleaned
                and cleaned not in matches
            ):
                matches.append(cleaned)

    if not matches:
        return None

    # Keep the UI readable.
    return " ".join(
        matches[:3]
    )[:700]



# ==========================================================
# PREVIOUS CYCLE REFERENCE
# ==========================================================

def official_domain_family(url: str) -> Optional[str]:
    """
    Return a practical parent domain so archived/previous-cycle
    pages can be matched to the same official institution.

    Examples:
        en.snu.ac.kr       -> snu.ac.kr
        www.u-tokyo.ac.jp  -> u-tokyo.ac.jp
        www.daad.de        -> daad.de
    """

    try:
        host = urlparse(url or "").netloc.lower()
    except Exception:
        return None

    host = host.split(":")[0]

    if not host:
        return None

    parts = host.split(".")

    three_part_suffixes = {
        "ac.kr",
        "go.kr",
        "edu.cn",
        "gov.cn",
        "ac.jp",
        "go.jp",
        "edu.tw",
        "gov.tw",
        "edu.my",
        "gov.my",
        "edu.sg",
        "gov.sg",
        "edu.hk",
        "gov.hk",
    }

    if len(parts) >= 3:
        suffix = ".".join(parts[-2:])

        if suffix in three_part_suffixes:
            return ".".join(parts[-3:])

    if len(parts) >= 2:
        return ".".join(parts[-2:])

    return host


def infer_cycle_year(
    scholarship: Scholarship,
    text: str,
) -> int:
    """
    Infer the current/upcoming scholarship cycle year.

    If the scholarship title/source explicitly contains a year
    such as 2027, use it. Otherwise use the current calendar year.
    """

    current_year = datetime.now().year

    source = " ".join(
        [
            scholarship.scholarship_name or "",
            scholarship.source_title or "",
            scholarship.source_snippet or "",
            text[:2500] if text else "",
        ]
    )

    years = []

    for match in re.findall(r"\b20\d{2}\b", source):
        try:
            year = int(match)

            # Keep only years reasonably close to the current cycle.
            if current_year - 2 <= year <= current_year + 3:
                years.append(year)

        except ValueError:
            pass

    if years:
        # Prefer the newest explicitly mentioned cycle.
        return max(years)

    return current_year


def candidate_previous_cycle_score(
    scholarship: Scholarship,
    result: dict,
    previous_cycle_year: int,
) -> int:
    title = result.get("title", "") or ""
    content = result.get("content", "") or ""
    url = result.get("url", "") or ""

    combined = (
        title
        + " "
        + content
        + " "
        + url
    ).lower()

    score = 0

    if str(previous_cycle_year) in combined:
        score += 6

    for term in [
        "application",
        "admission",
        "deadline",
        "application period",
        "scholarship",
        "graduate",
        "international",
    ]:
        if term in combined:
            score += 1

    # Reward overlap with meaningful words in scholarship name.
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "scholarship",
        "scholarships",
        "graduate",
        "admission",
        "admissions",
        "international",
        "university",
        "school",
    }

    name_words = [
        word.lower()
        for word in re.findall(
            r"[A-Za-z0-9]+",
            scholarship.scholarship_name or "",
        )
        if len(word) >= 4
        and word.lower() not in stop_words
    ]

    for word in name_words[:8]:
        if word in combined:
            score += 1

    if scholarship.university:
        university_words = [
            word.lower()
            for word in re.findall(
                r"[A-Za-z0-9]+",
                scholarship.university,
            )
            if len(word) >= 4
        ]

        for word in university_words[:5]:
            if word in combined:
                score += 1

    return score


def extract_single_source(
    client,
    url: str,
    query: str,
) -> Tuple[str, bool]:
    """
    Try to extract one official source.
    Returns (text, fully_extracted).
    """

    depths = (
        ["advanced"]
        if ".pdf" in url.lower()
        else ["basic", "advanced"]
    )

    for depth in depths:
        try:
            response = client.extract(
                urls=[url],
                extract_depth=depth,
                format="text",
                timeout=60,
                query=query,
                chunks_per_source=5,
            )

            results = response.get(
                "results",
                [],
            )

            if results:
                raw_content = (
                    results[0].get(
                        "raw_content",
                        "",
                    )
                    or ""
                )

                if len(raw_content) > 100:
                    return raw_content, True

        except TavilyTimeoutError:
            continue

        except Exception:
            continue

    return "", False


def find_previous_cycle_reference(
    scholarship: Scholarship,
    client,
    current_text: str,
) -> Tuple[
    Optional[int],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[bool],
    Optional[str],
]:
    """
    Find the most recent previous-cycle application dates from
    the same official institution/domain.

    Returns:
        previous_cycle_year
        previous_opening_date
        previous_deadline
        previous_cycle_source_url
        previous_source_extracted
        note
    """

    if not scholarship.official_url:
        return (
            None,
            None,
            None,
            None,
            None,
            "Previous-cycle lookup skipped because no official URL is available.",
        )

    domain = official_domain_family(
        scholarship.official_url
    )

    if not domain:
        return (
            None,
            None,
            None,
            None,
            None,
            "Previous-cycle lookup skipped because the official domain could not be determined.",
        )

    current_cycle_year = infer_cycle_year(
        scholarship,
        current_text,
    )

    previous_cycle_year = (
        current_cycle_year - 1
    )

    university_text = (
        scholarship.university
        or ""
    )

    query = (
        f"{scholarship.scholarship_name} "
        f"{university_text} "
        f"{scholarship.country or ''} "
        f"{previous_cycle_year} "
        f"application period opening date deadline "
        f"site:{domain}"
    )

    print(
        f"   🔎 Looking for previous cycle "
        f"({previous_cycle_year}) on {domain}..."
    )

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=6,
        )

    except Exception as error:
        return (
            None,
            None,
            None,
            None,
            None,
            f"Previous-cycle search failed: {error}",
        )

    candidates = []

    for result in response.get(
        "results",
        [],
    ):
        result_url = (
            result.get("url")
            or ""
        )

        if not result_url:
            continue

        result_domain = official_domain_family(
            result_url
        )

        # Only use the same official institution/domain family.
        if result_domain != domain:
            continue

        combined = (
            (result.get("title", "") or "")
            + " "
            + (result.get("content", "") or "")
            + " "
            + result_url
        )

        # The result should explicitly refer to the target
        # previous cycle year to reduce false matches.
        if str(previous_cycle_year) not in combined:
            continue

        score = candidate_previous_cycle_score(
            scholarship,
            result,
            previous_cycle_year,
        )

        candidates.append(
            (
                score,
                result,
            )
        )

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    if not candidates:
        return (
            None,
            None,
            None,
            None,
            None,
            (
                f"No reliable official previous-cycle "
                f"source found for {previous_cycle_year}."
            ),
        )

    extraction_query = (
        f"{previous_cycle_year} scholarship application "
        f"opening date application period deadline"
    )

    # Try the strongest official results first.
    for _, result in candidates[:4]:
        result_url = (
            result.get("url")
            or ""
        )

        result_content = (
            result.get("content")
            or ""
        )

        extracted_text, fully_extracted = (
            extract_single_source(
                client,
                result_url,
                extraction_query,
            )
        )

        previous_text = clean_text(
            extracted_text
            or result_content
        )

        if len(previous_text) < 50:
            continue

        (
            previous_opening_date,
            previous_deadline,
            previous_date_note,
        ) = extract_application_dates(
            previous_text
        )

        if (
            previous_opening_date is not None
            or previous_deadline is not None
        ):
            note = (
                f"Previous-cycle reference found for "
                f"{previous_cycle_year}."
            )

            if previous_date_note:
                note += (
                    " "
                    + previous_date_note
                )

            return (
                previous_cycle_year,
                previous_opening_date,
                previous_deadline,
                result_url,
                fully_extracted,
                note,
            )

    return (
        None,
        None,
        None,
        None,
        None,
        (
            f"Official previous-cycle pages were found for "
            f"{previous_cycle_year}, but application dates "
            f"could not be confidently extracted."
        ),
    )


# ==========================================================
# EXTRACT OFFICIAL PAGES
# ==========================================================

def extract_sources(
    scholarships: List[Scholarship],
) -> dict:
    urls = []

    for scholarship in scholarships:
        if (
            scholarship.official_url
            and scholarship.official_url not in urls
        ):
            urls.append(
                scholarship.official_url
            )

    if not urls:
        return {}

    print(
        f"\n🌐 Extracting "
        f"{len(urls)} official sources..."
    )

    client = get_tavily_client()

    content_map = {}

    # Small batches are more reliable.
    BATCH_SIZE = 2

    query = (
        "scholarship graduate admission application opening date "
        "application period deadline eligibility minimum GPA CGPA "
        "IELTS TOEFL English language requirement bachelor degree "
        "tuition stipend funding scholarship benefits"
    )

    for start in range(
        0,
        len(urls),
        BATCH_SIZE,
    ):
        batch = urls[
            start:
            start + BATCH_SIZE
        ]

        print(
            f"\n📡 Extracting batch "
            f"{start // BATCH_SIZE + 1}:"
        )

        for url in batch:
            print(
                f"   → {url}"
            )

        try:
            response = client.extract(
                urls=batch,
                extract_depth="basic",
                format="text",
                timeout=60,
                query=query,
                chunks_per_source=5,
            )

            for result in response.get(
                "results",
                [],
            ):
                url = result.get("url")
                raw_content = result.get(
                    "raw_content",
                    "",
                )

                if (
                    url
                    and raw_content
                    and len(raw_content) > 100
                ):
                    content_map[
                        url
                    ] = raw_content

        except TavilyTimeoutError:
            print(
                "⚠️ Batch timed out. "
                "Will retry URLs individually."
            )

        except Exception as error:
            print(
                f"⚠️ Batch extraction failed: "
                f"{error}"
            )

    # ------------------------------------------------------
    # Retry every URL that was not successfully extracted.
    # ------------------------------------------------------
    retry_urls = [
        url
        for url in urls
        if url not in content_map
    ]

    retry_urls = list(
        dict.fromkeys(
            retry_urls
        )
    )

    for url in retry_urls:
        print(
            "\n🔁 Retrying individually:"
        )
        print(
            f"   {url}"
        )

        if ".pdf" in url.lower():
            depths = [
                "advanced",
            ]
        else:
            depths = [
                "basic",
                "advanced",
            ]

        extracted = False

        for depth in depths:
            try:
                print(
                    f"   Trying {depth} extraction..."
                )

                response = client.extract(
                    urls=[url],
                    extract_depth=depth,
                    format="text",
                    timeout=60,
                    query=query,
                    chunks_per_source=5,
                )

                results = response.get(
                    "results",
                    [],
                )

                if results:
                    raw_content = (
                        results[0].get(
                            "raw_content",
                            "",
                        )
                    )

                    if (
                        raw_content
                        and len(raw_content) > 100
                    ):
                        content_map[
                            url
                        ] = raw_content

                        extracted = True

                        print(
                            "   ✅ Extraction succeeded."
                        )

                        break

            except TavilyTimeoutError:
                print(
                    f"   ⏱️ {depth} extraction timed out."
                )

            except Exception as error:
                print(
                    f"   ⚠️ {depth} extraction error: "
                    f"{error}"
                )

        if not extracted:
            print(
                "   ⚠️ Could not extract this source."
            )

    print(
        f"\n✅ Successfully extracted "
        f"{len(content_map)} / "
        f"{len(urls)} official sources."
    )

    return content_map


# ==========================================================
# VERIFY / ENRICH SCHOLARSHIPS
# ==========================================================

def verify_scholarship_sources(
    scholarships: List[Scholarship],
):
    print(
        "\n🔍 Real Evidence Agent started..."
    )

    content_map = extract_sources(
        scholarships
    )

    verified_scholarships = []
    evidence_records = []

    # Created lazily only when a scholarship is missing
    # a current/upcoming opening date or deadline.
    previous_cycle_client = None

    for scholarship in scholarships:
        print(
            "\n🔎 Checking:",
            scholarship.scholarship_name,
        )

        official_content = content_map.get(
            scholarship.official_url,
            "",
        )

        official_source_extracted = bool(
            official_content
            and len(
                clean_text(
                    official_content
                )
            ) >= 100
        )

        # If extraction failed, use the discovery snippet only
        # as secondary/fallback evidence.
        source_text = (
            official_content
            or scholarship.source_snippet
            or ""
        )

        text = clean_text(
            source_text
        )

        notes = []

        # ----------------------------------------
        # No useful content
        # ----------------------------------------
        if len(text) < 100:
            notes.append(
                "Official source could not be "
                "extracted sufficiently."
            )

            updated = scholarship.model_copy(
                update={
                    "source_verified":
                        official_source_extracted,
                    "verification_notes":
                        notes,
                }
            )

            verified_scholarships.append(
                updated
            )

            continue

        if not official_source_extracted:
            notes.append(
                "Full official source could not be extracted. "
                "Discovery snippet was used only as fallback evidence."
            )

        # ----------------------------------------
        # Extract structured fields
        # ----------------------------------------
        ielts, ielts_note = extract_ielts(
            text
        )

        ielts_required = (
            extract_ielts_required(
                text,
                ielts,
            )
        )

        toefl, toefl_note = extract_toefl(
            text
        )

        cgpa, cgpa_scale, cgpa_note = (
            extract_cgpa(
                text
            )
        )

        required_degree = (
            extract_required_degree(
                text
            )
        )

        english_waiver = (
            extract_english_waiver(
                text
            )
        )

        (
            opening_date,
            deadline,
            date_note,
        ) = extract_application_dates(
            text
        )

        # ----------------------------------------
        # Previous-cycle reference
        # ----------------------------------------
        previous_cycle_year = None
        previous_opening_date = None
        previous_deadline = None
        previous_cycle_source_url = None
        previous_source_extracted = None
        previous_cycle_note = None

        # Only look backward when current/upcoming application
        # timing is incomplete.
        if (
            opening_date is None
            or deadline is None
        ):
            if previous_cycle_client is None:
                previous_cycle_client = (
                    get_tavily_client()
                )

            (
                previous_cycle_year,
                previous_opening_date,
                previous_deadline,
                previous_cycle_source_url,
                previous_source_extracted,
                previous_cycle_note,
            ) = find_previous_cycle_reference(
                scholarship,
                previous_cycle_client,
                text,
            )

        funding = extract_funding(
            text
        )

        # ----------------------------------------
        # Notes
        # ----------------------------------------
        if ielts_note:
            notes.append(
                ielts_note
            )

        if toefl_note:
            notes.append(
                toefl_note
            )

        if cgpa_note:
            notes.append(
                cgpa_note
            )

        if date_note:
            notes.append(
                date_note
            )

        if previous_cycle_note:
            notes.append(
                previous_cycle_note
            )

        if funding is None:
            notes.append(
                "Funding details were not "
                "confidently extracted."
            )

        # ----------------------------------------
        # Update requirements
        # ----------------------------------------
        requirements = (
            scholarship.requirements
            .model_copy(
                update={
                    "minimum_cgpa":
                        cgpa,

                    "cgpa_scale":
                        cgpa_scale,

                    "required_degree":
                        required_degree,

                    # Do not guess the academic field.
                    "required_field":
                        scholarship
                        .requirements
                        .required_field,

                    "ielts_required":
                        ielts_required,

                    "minimum_ielts":
                        ielts,

                    "minimum_toefl":
                        toefl,

                    "english_waiver_possible":
                        english_waiver,
                }
            )
        )

        # ----------------------------------------
        # Update scholarship
        # ----------------------------------------
        updated = scholarship.model_copy(
            update={
                "requirements":
                    requirements,

                "opening_date":
                    opening_date,

                "deadline":
                    deadline,

                "previous_cycle_year":
                    previous_cycle_year,

                "previous_opening_date":
                    previous_opening_date,

                "previous_deadline":
                    previous_deadline,

                "previous_cycle_source_url":
                    previous_cycle_source_url,

                "funding_details":
                    (
                        funding
                        or scholarship.funding_details
                    ),

                "source_verified":
                    official_source_extracted,

                "verification_notes":
                    notes,
            }
        )

        verified_scholarships.append(
            updated
        )

        # ----------------------------------------
        # Evidence record
        # ----------------------------------------
        evidence_records.append(
            EvidenceRecord(
                scholarship_name=(
                    scholarship.scholarship_name
                ),

                claim=(
                    "Official scholarship source"
                ),

                source_url=(
                    scholarship.official_url
                ),

                source_type=(
                    "official_web"
                ),

                verified=(
                    official_source_extracted
                ),

                evidence_text=(
                    "Official source was "
                    "successfully extracted."
                    if official_source_extracted
                    else
                    "Official URL was discovered, but full source "
                    "extraction failed. Search snippet used as fallback."
                ),

                conflict_detected=(
                    any(
                        (
                            "Multiple" in note
                            or "multiple" in note
                        )
                        for note in notes
                    )
                ),
            )
        )

        if (
            previous_cycle_source_url
            and (
                previous_opening_date
                or previous_deadline
            )
        ):
            evidence_records.append(
                EvidenceRecord(
                    scholarship_name=(
                        scholarship.scholarship_name
                    ),
                    claim=(
                        f"Previous cycle "
                        f"{previous_cycle_year} application dates"
                    ),
                    source_url=(
                        previous_cycle_source_url
                    ),
                    source_type=(
                        "official_previous_cycle"
                    ),
                    verified=bool(
                        previous_source_extracted
                    ),
                    evidence_text=(
                        "Previous-cycle dates were found "
                        "on an official source from the "
                        "same institution/domain."
                    ),
                    conflict_detected=False,
                )
            )

        print(
            f"   Opening date: "
            f"{opening_date}"
        )

        print(
            f"   Deadline: "
            f"{deadline}"
        )

        if previous_cycle_year:
            print(
                f"   Previous cycle: "
                f"{previous_cycle_year}"
            )
            print(
                f"   Previous opening date: "
                f"{previous_opening_date}"
            )
            print(
                f"   Previous deadline: "
                f"{previous_deadline}"
            )
            print(
                f"   Previous source: "
                f"{previous_cycle_source_url}"
            )


        print(
            f"   IELTS required: "
            f"{ielts_required}"
        )

        print(
            f"   IELTS minimum: "
            f"{ielts}"
        )

        print(
            f"   TOEFL minimum: "
            f"{toefl}"
        )

        print(
            f"   CGPA: "
            f"{cgpa}"
        )

        print(
            f"   Degree: "
            f"{required_degree}"
        )

        print(
            f"   Funding found: "
            f"{funding is not None}"
        )

    print(
        f"\n✅ Real Evidence Agent processed "
        f"{len(verified_scholarships)} "
        f"scholarships."
    )

    return (
        verified_scholarships,
        evidence_records,
    )


# ==========================================================
# MANUAL TEST
# ==========================================================

if __name__ == "__main__":
    from agents.profile_agent import (
        build_profile,
    )

    from agents.discovery_agent import (
        discover_scholarships,
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

    verified, evidence = (
        verify_scholarship_sources(
            scholarships
        )
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "REAL VERIFIED SCHOLARSHIP DATA"
    )

    print(
        "=" * 70
    )

    for scholarship in verified:
        print(
            f"\n🎓 "
            f"{scholarship.scholarship_name}"
        )

        print(
            f"URL: "
            f"{scholarship.official_url}"
        )

        print(
            f"Source verified: "
            f"{scholarship.source_verified}"
        )

        print(
            f"Opening date: "
            f"{scholarship.opening_date}"
        )

        print(
            f"Deadline: "
            f"{scholarship.deadline}"
        )

        print(
            f"Previous cycle year: "
            f"{scholarship.previous_cycle_year}"
        )

        print(
            f"Previous opening date: "
            f"{scholarship.previous_opening_date}"
        )

        print(
            f"Previous deadline: "
            f"{scholarship.previous_deadline}"
        )

        print(
            f"Previous cycle source: "
            f"{scholarship.previous_cycle_source_url}"
        )


        print(
            f"IELTS required: "
            f"{scholarship.requirements.ielts_required}"
        )

        print(
            f"Minimum IELTS: "
            f"{scholarship.requirements.minimum_ielts}"
        )

        print(
            f"Minimum TOEFL: "
            f"{scholarship.requirements.minimum_toefl}"
        )

        print(
            f"Minimum CGPA: "
            f"{scholarship.requirements.minimum_cgpa}"
        )

        print(
            f"Required Degree: "
            f"{scholarship.requirements.required_degree}"
        )

        print(
            f"Funding: "
            f"{scholarship.funding_details}"
        )

        print(
            "Verification Notes:"
        )

        for note in (
            scholarship.verification_notes
        ):
            print(
                f"  ⚠️ {note}"
            )
