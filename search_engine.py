import pickle
import sqlite3
import faiss
import os

from sentence_transformers import SentenceTransformer
from scorer import skill_score, experience_score, skill_analysis
from jd_parser import extract_experience

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

index = faiss.read_index(
    "resume_index.faiss"
)

with open(
    "resume_metadata.pkl",
    "rb"
) as f:

    filenames = pickle.load(f)


def search_candidates(jd, top_k=100):

    conn = sqlite3.connect(
        "candidate.db"
    )

    cursor = conn.cursor()

    query_embedding = model.encode([jd])

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    jd_exp = extract_experience(jd)

    results = []

    for rank, idx in enumerate(indices[0]):

        if idx == -1:
            continue

        filepath = filenames[idx]

        cursor.execute(
            """
            SELECT
                name,
                email,
                phone,
                experience,
                resume_text
            FROM candidates
            WHERE filepath=?
            LIMIT 1
            """,
            (filepath,)
        )

        row = cursor.fetchone()

        if not row:
            continue

        semantic_score = round(
            (1 / (1 + distances[0][rank])) * 100,
            2
        )

        skill_match = skill_score(
            jd,
            row[4]
        )

        matched_skills, missing_skills = skill_analysis(
    jd,
    row[4]
)

        exp_match = experience_score(
            jd_exp,
            row[3]
        )

        final_score = round(
            semantic_score * 0.70 +
            skill_match * 0.20 +
            exp_match * 0.10,
            2
        )

        results.append(
            {
                "name": row[0],
                "email": row[1],
                "phone": row[2],
                "experience": row[3],
                "resume": os.path.basename(filepath),
                "filepath": filepath,
                "semantic_score": semantic_score,
                "skill_score": round(skill_match, 2),
                "experience_score": round(exp_match, 2),
                "final_score": final_score,
                "matched_skills": matched_skills,
"missing_skills": missing_skills,
            }
        )

    conn.close()

    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return results