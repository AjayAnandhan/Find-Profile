from jd_parser import (
    extract_skills,
)


def skill_score(
    jd,
    resume_text
):

    jd_skills = extract_skills(jd)

    if not jd_skills:
        return 0

    resume_lower = resume_text.lower()

    matched = 0

    for skill in jd_skills:

        if skill.lower() in resume_lower:
            matched += 1

    return (
        matched /
        len(jd_skills)
    ) * 100


def skill_analysis(
    jd,
    resume_text
):

    jd_skills = extract_skills(jd)

    resume_lower = resume_text.lower()

    matched_skills = []
    missing_skills = []

    for skill in jd_skills:

        if skill.lower() in resume_lower:

            matched_skills.append(
                skill
            )

        else:

            missing_skills.append(
                skill
            )

    return (
        matched_skills,
        missing_skills
    )


def experience_score(
    jd_exp,
    candidate_exp
):

    if jd_exp == 0:
        return 100

    score = (
        candidate_exp /
        jd_exp
    ) * 100

    return min(score, 100)