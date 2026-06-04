import sqlite3

conn = sqlite3.connect("candidate.db")

cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM candidates")

count = cursor.fetchone()[0]

print(f"Total Resumes: {count}")

conn.close()
