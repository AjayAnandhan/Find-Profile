import json
import re
from pathlib import Path


SKILLS_FILE = Path("skills.json")

STOP_WORDS = {
    "need",
    "needs",
    "required",
    "requirement",
    "senior",
    "junior",
    "engineer",
    "developer",
    "architect",
    "consultant",
    "with",
    "for",
    "and",
    "or",
    "the",
    "a",
    "an",
    "years",
    "year",
    "experience",
    "must",
    "have",
    "strong",
    "job",
    "description",
    "responsibilities",
    "requirements",
    "preferred",
    "candidate",
    "role",
    "node",
    "js",
}

SKILL_ALIASES = {
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "k8s": "kubernetes",
    "node.js": "nodejs",
    "node js": "nodejs",
    "postgres": "postgresql",
    "postgre sql": "postgresql",
    "ms sql": "sql server",
    "mssql": "sql server",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "artificial intelligence": "ai",
    "machine-learning": "machine learning",
    "sd-wan": "sdwan",
    "argo cd": "argocd",
}

FALLBACK_PATTERNS = [
    r"\b[A-Z]{2,}\b",
    r"\b[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?\b",
    r"\b[A-Za-z]+-[A-Za-z]+\b",
    r"\b[A-Za-z]+(?:\.[A-Za-z]+)+\b",
    r"\b[A-Za-z]+\+[A-Za-z]+\b",
    r"\b[A-Za-z]+#\b",
]


def normalize_skill(skill):

    normalized = re.sub(r"\s+", " ", skill.strip().lower())

    return SKILL_ALIASES.get(normalized, normalized)


def load_skills():

    if not SKILLS_FILE.exists():
        return {}

    try:
        with SKILLS_FILE.open("r", encoding="utf-8") as file:
            skills = json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}

    return {
        normalize_skill(skill): value
        for skill, value in skills.items()
    }


def save_skills(skills):

    ordered_skills = {
        skill: skills[skill]
        for skill in sorted(skills)
    }

    with SKILLS_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            ordered_skills,
            file,
            indent=4
        )
        file.write("\n")


def extract_experience(jd):

    patterns = [
        r"(\d+)\s*(?:-|to)\s*\d+\s*(?:years|yrs)",
        r"(?:minimum|min|at least)\s*(\d+)\s*(?:years|yrs)",
        r"(\d+)\s*(?:\+|plus)?\s*(?:years|yrs)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            jd,
            re.IGNORECASE
        )

        if match:
            return int(match.group(1))

    return 0


def _contains_skill(text, skill):

    escaped_skill = re.escape(skill)
    pattern = rf"(?<![a-z0-9+#.]){escaped_skill}(?![a-z0-9+#.])"

    return re.search(pattern, text, re.IGNORECASE) is not None


def _extract_known_skills(jd, known_skills):

    text = jd.lower()
    matched = set()

    for skill in known_skills:

        if _contains_skill(text, skill):
            matched.add(skill)

    for alias, canonical_skill in SKILL_ALIASES.items():

        if canonical_skill in known_skills and _contains_skill(text, alias):
            matched.add(canonical_skill)

    return matched


def _extract_fallback_skills(jd):

    fallback_skills = set()

    for pattern in FALLBACK_PATTERNS:

        for match in re.findall(pattern, jd):

            skill = normalize_skill(match)

            if len(skill) < 2:
                continue

            if skill in STOP_WORDS:
                continue

            if any(token in STOP_WORDS for token in skill.split()):
                continue

            fallback_skills.add(skill)

    return fallback_skills


def analyze_jd_skills(jd):

    known_skills = load_skills()
    known_skill_names = set(known_skills)
    matched_known = _extract_known_skills(jd, known_skill_names)
    fallback_skills = _extract_fallback_skills(jd)
    unknown_skills = fallback_skills - matched_known - known_skill_names

    return {
        "known": sorted(matched_known),
        "unknown": sorted(unknown_skills),
        "all": sorted(matched_known | unknown_skills),
    }


def extract_skills(jd):

    return analyze_jd_skills(jd)["all"]


def add_skills_to_json(skills):

    existing_skills = load_skills()
    added_skills = []

    for skill in skills:

        normalized_skill = normalize_skill(skill)

        if not normalized_skill:
            continue

        if normalized_skill in STOP_WORDS:
            continue

        if normalized_skill not in existing_skills:
            existing_skills[normalized_skill] = 0
            added_skills.append(normalized_skill)

    if added_skills:
        save_skills(existing_skills)

    return sorted(added_skills)
