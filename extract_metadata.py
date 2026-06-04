import os
import re
import fitz
import sqlite3

from docx import Document
from config import RESUME_FOLDER

success_count = 0
error_count = 0

# ----------------------------
# Resume Readers
# ----------------------------


def read_pdf(path):

    text = ""

    pdf = fitz.open(path)

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text


def read_docx(path):

    doc = Document(path)

    return "\n".join(p.text for p in doc.paragraphs)


# ----------------------------
# Extractors
# ----------------------------


def extract_email(text):

    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)

    return match.group(0) if match else ""


def extract_phone(text):

    match = re.search(r"(\+?\d[\d\-\(\)\s]{8,})", text)

    return match.group(0).strip() if match else ""


def extract_name(text):

    lines = text.splitlines()

    for line in lines:
        line = line.strip()

        if len(line) > 3:
            return line

    return ""


def extract_experience(text):

    patterns = [r"(\d+)\+?\s+years", r"(\d+)\+?\s+yrs"]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return float(match.group(1))

    return 0


# ----------------------------
# Database
# ----------------------------

conn = sqlite3.connect("candidate.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    experience REAL,
    filename TEXT,
    filepath TEXT UNIQUE,
    resume_text TEXT
)
""")

# ----------------------------
# Process Resumes
# ----------------------------

resume_folder = RESUME_FOLDER

for root, dirs, files in os.walk(RESUME_FOLDER):
    for file in files:
        if not file.lower().endswith((".pdf", ".docx")):
            continue

        filepath = os.path.join(root, file)

        if not os.path.isfile(filepath):
            continue

        if file.startswith("~"):
            continue

        if file.startswith("~$"):
            continue

        try:
            print(f"Checking: {filepath}")

            if file.lower().endswith(".pdf"):
                text = read_pdf(filepath)

            else:
                text = read_docx(filepath)

            name = extract_name(text)
            email = extract_email(text)
            phone = extract_phone(text)
            experience = extract_experience(text)

            cursor.execute(
                """
                INSERT OR REPLACE INTO candidates
                (
                    name,
                    email,
                    phone,
                    experience,
                    filename,
                    filepath,
                    resume_text
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (name, email, phone, experience, file, filepath, text),
            )
            success_count += 1
            print(f"Added: {file}")

        except Exception as e:
            error_count += 1
            print(f"Error processing {file}: {e}")

conn.commit()

conn.close()

print("\nMetadata extraction completed.")
print("SUCCESS:", success_count)
print("ERRORS :", error_count)
