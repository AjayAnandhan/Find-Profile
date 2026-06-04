import os
import re
import fitz
import sqlite3

from docx import Document

# ----------------------------
# Resume Readers
# ----------------------------

def read_pdf(path):

    text = ""

    pdf = fitz.open(path)

    for page in pdf:
        text += page.get_text()

    return text


def read_docx(path):

    doc = Document(path)

    return "\n".join(
        p.text for p in doc.paragraphs
    )

# ----------------------------
# Extractors
# ----------------------------

def extract_email(text):

    match = re.search(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        text
    )

    return match.group(0) if match else ""


def extract_phone(text):

    match = re.search(
        r'(\+?\d[\d\-\(\)\s]{8,})',
        text
    )

    return match.group(0).strip() if match else ""


def extract_name(text):

    lines = text.splitlines()

    for line in lines:

        line = line.strip()

        if len(line) > 3:
            return line

    return ""


def extract_experience(text):

    patterns = [
        r'(\d+)\+?\s+years',
        r'(\d+)\+?\s+yrs'
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return float(match.group(1))

    return 0


# ----------------------------
# Database
# ----------------------------

conn = sqlite3.connect(
    "candidate.db"
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates
(
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    phone TEXT,
    experience REAL,
    filename TEXT
)
""")

# ----------------------------
# Process Resumes
# ----------------------------

resume_folder = "resumes"

for file in os.listdir(resume_folder):

    filepath = os.path.join(
        resume_folder,
        file
    )

    try:

        if file.lower().endswith(".pdf"):
            text = read_pdf(filepath)

        elif file.lower().endswith(".docx"):
            text = read_docx(filepath)

        else:
            continue

        name = extract_name(text)
        email = extract_email(text)
        phone = extract_phone(text)
        experience = extract_experience(text)

        cursor.execute(
            """
            INSERT INTO candidates
            (
                name,
                email,
                phone,
                experience,
                filename
            )
            VALUES
            (
                ?, ?, ?, ?, ?
            )
            """,
            (
                name,
                email,
                phone,
                experience,
                file
            )
        )

        print(
            f"Added: {name}"
        )

    except Exception as e:

        print(
            file,
            e
        )

conn.commit()

conn.close()

print("\nMetadata extraction completed.")
