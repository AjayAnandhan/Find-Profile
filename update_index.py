import os
import pickle
import faiss
import fitz
import numpy as np
import sqlite3
import re
import os
import sys

sys.stdout.reconfigure(
    encoding="utf-8"
)

from docx import Document
from sentence_transformers import SentenceTransformer

from config import RESUME_FOLDER

# ----------------------------

# Readers

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

# Load Existing FAISS

# ----------------------------

index = faiss.read_index("resume_index.faiss")

with open("resume_metadata.pkl", "rb") as f:
    stored_paths = pickle.load(f)

stored_paths = set(stored_paths)

# ----------------------------

# Find New Resumes

# ----------------------------

new_files = []

for root, dirs, files in os.walk(RESUME_FOLDER):
    for file in files:

        if file.startswith("~"):
            continue

        if file.startswith("~$"):
            continue

        if not file.lower().endswith((".pdf", ".docx")):
            continue

        filepath = os.path.join(root, file)

        if filepath not in stored_paths:
            new_files.append(filepath)

print(f"Found {len(new_files)} new resumes")

for file in new_files:
    print(file)

if len(new_files) == 0:
    print("No new resumes found.")

    exit()

# ----------------------------

# Load Model

# ----------------------------

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# ----------------------------

# Read New Resumes

# ----------------------------


conn = sqlite3.connect("candidate.db")

cursor = conn.cursor()
documents = []

for filepath in new_files:
    try:
        if filepath.lower().endswith(".pdf"):
            text = read_pdf(filepath)

        else:
            text = read_docx(filepath)
            
        documents.append(text)

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
            (
                name,
                email,
                phone,
                experience,
                os.path.basename(filepath),
                filepath,
                text,
            ),
        )

        print(f"Loaded: {os.path.basename(filepath)}")

    except Exception as e:
        print(f"Error: {filepath}")

        print(e)

# ----------------------------

# Create Embeddings

# ----------------------------

embeddings = model.encode(documents, convert_to_numpy=True)

embeddings = embeddings.astype(np.float32)

# ----------------------------

# Update FAISS

# ----------------------------

index.add(embeddings)

faiss.write_index(index, "resume_index.faiss")

# ----------------------------

# Update Metadata

# ----------------------------

stored_paths = list(stored_paths)

stored_paths.extend(new_files)

with open("resume_metadata.pkl", "wb") as f:
    pickle.dump(stored_paths, f)

conn.commit()

conn.close()

print(f"Added {len(new_files)} resumes.")

print("FAISS Updated Successfully.")
