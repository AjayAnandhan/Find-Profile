import sqlite3

conn = sqlite3.connect(
    "candidate.db"
)

cursor = conn.cursor()

cursor.execute("""
SELECT
    filename,
    LENGTH(resume_text)
FROM candidates
LIMIT 10
""")

for row in cursor.fetchall():
    print(row)

conn.close()