import streamlit as st

from search_engine import search_candidates
from jd_parser import extract_skills

st.set_page_config(
    page_title="Recruiter AI",
    layout="wide"
)

st.title("🔍 Recruiter AI")

jd = st.text_area(
    "Paste Job Description",
    height=250
)

if jd:
    st.write(extract_skills(jd))

if st.button("Search Candidates"):

    if jd:

        results = search_candidates(jd)

        for candidate in results:

            st.markdown("---")

            st.subheader(
                candidate["name"]
            )

            st.write(
                f"🏆 Final Score: {candidate['final_score']}%"
            )

            st.write(
                f"🧠 Semantic Match: {candidate['semantic_score']}%"
            )

            st.write(
                f"🛠️ Skill Match: {candidate['skill_score']}%"
            )

            st.write(
                f"📈 Experience Match: {candidate['experience_score']}%"
            )
            
            st.write("✅ Matched Skills")

            st.write(
                ", ".join(candidate["matched_skills"])
            )

            st.write("❌ Missing Skills")

            st.write(
                ", ".join(
                    candidate["missing_skills"]
                )
            )

            st.write(
                f"Experience: {candidate['experience']} years"
            )

            st.write(
                f"Email: {candidate['email']}"
            )

            st.write(
                f"Phone: {candidate['phone']}"
            )

            st.write(
                f"Resume: {candidate['resume']}"
            )