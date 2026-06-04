import os
import fitz
from docx import Document

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

        print("\n")
        print("=" * 60)
        print(file)
        print("=" * 60)

        print(text[:1000])

    except Exception as e:
        print(file, e)