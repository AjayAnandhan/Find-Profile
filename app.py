import streamlit as st
import subprocess
import sqlite3
import os
import sys

from search_engine import search_candidates
from jd_parser import extract_skills
from settings import load_settings, save_settings

conn = sqlite3.connect("candidate.db")

st.sidebar.write(f"DB Path = {os.path.abspath('candidate.db')}")

cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM candidates")

count = cursor.fetchone()[0]

st.sidebar.write(f"DB Count = {count}")

conn.close()

st.sidebar.markdown("---")

st.sidebar.write(f"📄 Total Resumes: {count}")

if st.sidebar.button("Update Resume Database"):
    with st.spinner("Updating..."):
        result = subprocess.run(
            [sys.executable, "extract_metadata.py"], capture_output=True, text=True
        )

    st.text(result.stdout)

    st.success("Database Updated")

    st.rerun()

if st.sidebar.button("♻️ Full Rebuild"):
    status = st.empty()
    with st.spinner("Rebuilding database..."):
        # Delete old files

        status.info("🗑️ Deleting old database files...")

        for file in ["candidate.db", "resume_index.faiss", "resume_metadata.pkl"]:
            if os.path.exists(file):
                try:
                    conn.close()
                except:
                    pass
                os.remove(file)

        # Recreate database
        status.info("📄 Extracting resume metadata...")
        subprocess.run([sys.executable, "extract_metadata.py"])

        # Recreate FAISS
        status.info("🧠 Building FAISS index...")
        subprocess.run([sys.executable, "build_index.py"])
    status.success(f"✅ Full Rebuild Completed\n\n📄 Total Resumes: {count}")
    st.success("Full Rebuild Completed")

    st.rerun()

settings = load_settings()

st.sidebar.header("⚙️ Settings")

resume_folder = st.sidebar.text_input(
    "Resume Folder", value=settings.get("resume_folder", "")
)

if st.sidebar.button("Save Path"):
    settings["resume_folder"] = resume_folder

    save_settings(settings)

    st.sidebar.success("Saved")

st.set_page_config(page_title="Recruiter AI", layout="wide")

st.title("🔍 Recruiter AI")

jd = st.text_area("Paste Job Description", height=250)

if jd:
    st.write(extract_skills(jd))

if st.button("Search Candidates"):
    if jd:
        results = search_candidates(jd)

        for candidate in results:
            st.markdown("---")

            st.subheader(candidate["name"])

            st.write(f"🏆 Final Score: {candidate['final_score']}%")

            st.write(f"🧠 Semantic Match: {candidate['semantic_score']}%")

            st.write(f"🛠️ Skill Match: {candidate['skill_score']}%")

            st.write(f"📈 Experience Match: {candidate['experience_score']}%")

            st.write("✅ Matched Skills")

            st.write(", ".join(candidate["matched_skills"]))

            st.write("❌ Missing Skills")

            st.write(", ".join(candidate["missing_skills"]))

            st.write(f"Experience: {candidate['experience']} years")

            st.write(f"Email: {candidate['email']}")

            st.write(f"Phone: {candidate['phone']}")

            st.write(f"Resume: {candidate['resume']}")
