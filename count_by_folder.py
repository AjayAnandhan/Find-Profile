# count_by_folder.py

import sqlite3
from collections import Counter
import os

conn = sqlite3.connect("candidate.db")

cursor = conn.cursor()

cursor.execute(
    "SELECT filepath FROM candidates"
)

counter = Counter()

for (path,) in cursor.fetchall():

    folder = os.path.dirname(path)

    counter[folder] += 1

conn.close()

for folder, count in counter.most_common(20):

    print(count, folder)