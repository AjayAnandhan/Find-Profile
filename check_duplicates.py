import sqlite3

conn = sqlite3.connect("candidate.db")

cursor = conn.cursor()

cursor.execute("""
SELECT COUNT(*)
FROM candidates
""")

print("Total Rows:",
      cursor.fetchone()[0])

cursor.execute("""
SELECT COUNT(DISTINCT filepath)
FROM candidates
""")

print("Unique Files:",
      cursor.fetchone()[0])

conn.close()