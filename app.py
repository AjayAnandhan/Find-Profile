import streamlit as st

from search_engine import search_candidates

st.set_page_config(
    page_title="Recruiter AI",
    layout="wide"
)

st.title("🔍 Recruiter AI")

jd = st.text_area(
    "Paste Job Description",
    height=250
)

if st.button("Search Candidates"):

    if jd:

        results = search_candidates(jd)

        for candidate in results:

            st.markdown("---")

            st.subheader(
                candidate["name"]
            )

            st.write(
                f"Match Score: {candidate['score']}%"
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