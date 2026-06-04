import os
import pickle
import fitz
import faiss

from docx import Document
from sentence_transformers import SentenceTransformer
from config import RESUME_FOLDER

MODEL_NAME = "BAAI/bge-small-en-v1.5"

model = SentenceTransformer(MODEL_NAME)

resume_files = []

for root, dirs, files in os.walk(RESUME_FOLDER):

    for file in files:

        if file.lower().endswith(
            (".pdf", ".docx")
        ):

            resume_files.append(
                os.path.join(
                    root,
                    file
                )
            )

documents = []
filenames = []


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


for filepath in resume_files:

    file = os.path.basename(
        filepath
    )

    try:

        if file.lower().endswith(".pdf"):
            text = read_pdf(filepath)

        elif file.lower().endswith(".docx"):
            text = read_docx(filepath)

        else:
            continue

        filenames.append(filepath)
        documents.append(text)

        print(f"Loaded: {file}")

    except Exception as e:

        print(
            f"Error: {file} - {e}"
        )

print("\nCreating embeddings...")

embeddings = model.encode(
    documents,
    show_progress_bar=True
)

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(embeddings)

faiss.write_index(
    index,
    "resume_index.faiss"
)

with open(
    "resume_metadata.pkl",
    "wb"
) as f:

    pickle.dump(
        filenames,
        f
    )

print("Index created successfully.")