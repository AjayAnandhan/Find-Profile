import sqlite3

conn = sqlite3.connect("candidate.db")

cursor = conn.cursor()

try:
    cursor.execute("""
    ALTER TABLE candidates
    ADD COLUMN skills TEXT
    """)
except:
    print("Column already exists")

conn.commit()
conn.close()

print("Done")