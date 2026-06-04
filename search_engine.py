import pickle
import sqlite3
import faiss

from sentence_transformers import SentenceTransformer

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


def search_candidates(jd, top_k=10):

    conn = sqlite3.connect(
        "candidate.db"
    )

    cursor = conn.cursor()

    query_embedding = model.encode(
        [jd]
    )

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for rank, idx in enumerate(
        indices[0],
        start=1
    ):

        filename = filenames[idx]

        cursor.execute(
            """
            SELECT
                name,
                email,
                phone,
                experience
            FROM candidates
            WHERE filename=?
            LIMIT 1
            """,
            (filename,)
        )

        row = cursor.fetchone()

        if row:

            score = round(
                (1 / (1 + distances[0][rank-1])) * 100,
                2
            )

            results.append(
                {
                    "score": score,
                    "name": row[0],
                    "email": row[1],
                    "phone": row[2],
                    "experience": row[3],
                    "resume": filename
                }
            )

    conn.close()

    return results