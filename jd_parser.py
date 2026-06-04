import re
import json

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
    "strong"
}


def extract_experience(jd):

    patterns = [
        r'(\d+)\+?\s*years',
        r'(\d+)\+?\s*yrs'
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


def extract_skills(jd):

    skills = set()

    # Technical words
    patterns = [

        r'\b[A-Z]{2,}\b',                 # AWS, BGP, OSPF, CCNP

        r'\b[A-Z][a-zA-Z]+\b',            # Cisco, Citrix

        r'\b[A-Z][a-zA-Z]+\s[A-Z][a-zA-Z]+\b',  # Direct Connect

        r'\b[A-Za-z]+-[A-Za-z]+\b',       # SD-WAN

        r'\b[A-Za-z]+\+[A-Za-z]+\b'       # C++
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            jd
        )

        for match in matches:

            word = match.strip()

            if len(word) < 3:
                continue

            if word.lower() in STOP_WORDS:
                continue

            skills.add(word)

    return sorted(list(skills))