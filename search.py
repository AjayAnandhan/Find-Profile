import pickle
import sqlite3
import faiss

from sentence_transformers import SentenceTransformer

# ------------------------
# Load Model
# ------------------------

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# ------------------------
# Load FAISS
# ------------------------

index = faiss.read_index("resume_index.faiss")

with open("resume_metadata.pkl", "rb") as f:
    filenames = pickle.load(f)

# ------------------------
# Database
# ------------------------

conn = sqlite3.connect("candidate.db")

cursor = conn.cursor()

# ------------------------
# JD Input
# ------------------------

print("\nPaste Job Description")
print("(Press Enter twice when done)")
print("-" * 50)

lines = []

while True:
    line = input()

    if line == "":
        break

    lines.append(line)

jd = "\n".join(lines)

# ------------------------
# Search
# ------------------------

query_embedding = model.encode([jd])

distances, indices = index.search(query_embedding, 100)

print("\n")
print("=" * 80)
print("TOP MATCHES")
print("=" * 80)

for rank, idx in enumerate(indices[0], start=1):
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
        (filename,),
    )

    candidate = cursor.fetchone()

    score = round((1 / (1 + distances[0][rank - 1])) * 100, 2)

    print("\n")
    print(f"Rank #{rank}")
    print(f"Match Score : {score}%")

    if candidate:
        print(f"Name        : {candidate[0]}")
        print(f"Email       : {candidate[1]}")
        print(f"Phone       : {candidate[2]}")
        print(f"Experience  : {candidate[3]} years")

    print(f"Resume      : {filename}")

conn.close()
