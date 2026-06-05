import streamlit as st
import subprocess
import sqlite3
import os
import sys
import html
import importlib
import json
import streamlit.components.v1 as components

from search_engine import search_candidates
import jd_parser
from settings import load_settings, save_settings

st.set_page_config(page_title="Recruiter AI", layout="wide")

jd_parser = importlib.reload(jd_parser)
add_skills_to_json = jd_parser.add_skills_to_json
analyze_jd_skills = jd_parser.analyze_jd_skills

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Urbanist:wght@400;500;600;700;800&display=swap');

        .stApp {
            background: #f7fbf8;
            color: #273b34;
            font-family: "Urbanist", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp * {
            font-family: "Urbanist", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #eefbf4 0%, #dff5ea 100%);
            border-right: 1px solid #d6efe2;
        }

        [data-testid="stSidebar"] * {
            color: #31594c;
        }

        [data-testid="stSidebar"] input {
            color: #273b34;
            background: #ffffff;
        }

        .block-container {
            padding-top: 2rem;
        }

        h1 {
            color: #233c34;
            font-weight: 800;
            letter-spacing: 0;
        }

        label,
        p,
        span,
        div {
            color: #415b52;
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
            border-color: #d6efe2;
            border-radius: 8px;
        }

        .stButton > button {
            border: 1px solid #b9e5d0;
            border-radius: 8px;
            background: #e7f8ef;
            color: #2f6f5d;
            font-weight: 800;
        }

        .stButton > button:hover {
            border-color: #8fd4b4;
            background: #d7f2e5;
            color: #245a4b;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def safe_text(value):

    if value is None:
        return ""

    return html.escape(str(value))


def safe_json(value):

    return html.escape(json.dumps(value), quote=True)


def render_candidate_table(results):

    rows = []

    for index, candidate in enumerate(results):

        name = safe_text(candidate.get("name", ""))
        email = safe_text(candidate.get("email", ""))
        phone = safe_text(candidate.get("phone", ""))
        skill_score = safe_text(candidate.get("skill_score", ""))
        final_score = safe_text(candidate.get("final_score", ""))
        resume = safe_text(candidate.get("resume", ""))
        semantic_score = safe_text(candidate.get("semantic_score", ""))
        experience_score = safe_text(candidate.get("experience_score", ""))
        experience = safe_text(candidate.get("experience", ""))
        matched_skills = safe_text(", ".join(candidate.get("matched_skills", [])))
        missing_skills = safe_text(", ".join(candidate.get("missing_skills", [])))

        rows.append(
            f"""
            <tr class="candidate-row">
                <td>
                    <button class="name-link" type="button" onclick="toggleDetails({index})">
                        {name}
                    </button>
                </td>
                <td>
                    <div class="copy-cell">
                        <span>{email}</span>
                        <button class="copy-btn" type="button" data-copy="{safe_json(candidate.get("email", ""))}">Copy</button>
                    </div>
                </td>
                <td>{phone}</td>
                <td data-value="{safe_text(candidate.get("skill_score", 0))}">
                    <span class="score-pill">{skill_score}%</span>
                </td>
                <td data-value="{safe_text(candidate.get("final_score", 0))}">
                    <span class="final-pill">{final_score}%</span>
                </td>
                <td>
                    <div class="copy-cell">
                        <span>{resume}</span>
                        <button class="copy-btn" type="button" data-copy="{safe_json(candidate.get("resume", ""))}">Copy</button>
                    </div>
                </td>
            </tr>
            <tr class="details-row" id="details-{index}">
                <td colspan="6">
                    <div class="details-panel">
                        <div>
                            <p class="details-label">Semantic Match</p>
                            <p class="details-value">{semantic_score}%</p>
                        </div>
                        <div>
                            <p class="details-label">Experience Match</p>
                            <p class="details-value">{experience_score}%</p>
                        </div>
                        <div>
                            <p class="details-label">Experience</p>
                            <p class="details-value">{experience} years</p>
                        </div>
                        <div>
                            <p class="details-label">Matched Skills</p>
                            <p class="details-value">{matched_skills}</p>
                        </div>
                        <div>
                            <p class="details-label">Missing Skills</p>
                            <p class="details-value">{missing_skills}</p>
                        </div>
                    </div>
                </td>
            </tr>
            """
        )

    table_rows = "\n".join(rows)

    components.html(
        f"""
        <div class="candidate-shell">
            <table id="candidate-table">
                <thead>
                    <tr>
                        <th data-type="text">Name <span>Sort</span></th>
                        <th data-type="text">Email <span>Sort</span></th>
                        <th data-type="text">Phone <span>Sort</span></th>
                        <th data-type="number">Skill Match <span>Sort</span></th>
                        <th data-type="number">Final Score <span>Sort</span></th>
                        <th data-type="text">Filename <span>Sort</span></th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <style>
            @import url('https://fonts.googleapis.com/css2?family=Urbanist:wght@400;500;600;700;800&display=swap');

            :root {{
                --green-900: #233c34;
                --green-800: #31594c;
                --green-700: #3b7d68;
                --green-100: #dff5ea;
                --green-50: #f1fbf6;
                --line: #dcefe6;
                --text: #273b34;
                --muted: #6d8178;
            }}

            * {{
                box-sizing: border-box;
                font-family: "Urbanist", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}

            body {{
                margin: 0;
                background: #f7fbf8;
                color: var(--text);
                font-family: "Urbanist", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}

            .candidate-shell {{
                max-height: 680px;
                overflow: auto;
                border: 1px solid var(--line);
                border-radius: 8px;
                background: #ffffff;
                box-shadow: 0 12px 28px rgba(31, 107, 85, 0.08);
            }}

            table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                min-width: 980px;
            }}

            thead th {{
                position: sticky;
                top: 0;
                z-index: 2;
                padding: 16px 18px;
                border-bottom: 1px solid var(--line);
                background: linear-gradient(180deg, #fbfffd 0%, #effbf5 100%);
                color: var(--green-900);
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0;
                text-align: left;
                text-transform: uppercase;
                white-space: nowrap;
                cursor: pointer;
                user-select: none;
            }}

            thead th span {{
                color: #8ca99d;
                font-size: 13px;
                margin-left: 6px;
            }}

            tbody td {{
                padding: 14px 18px;
                border-bottom: 1px solid #eef7f2;
                color: var(--text);
                font-size: 14px;
                vertical-align: middle;
            }}

            .candidate-row:hover td {{
                background: #f8fdfb;
            }}

            .name-link {{
                border: 0;
                background: transparent;
                color: var(--green-700);
                cursor: pointer;
                font: inherit;
                font-weight: 800;
                padding: 0;
                text-align: left;
            }}

            .name-link:hover {{
                color: var(--green-900);
                text-decoration: underline;
            }}

            .copy-cell {{
                align-items: center;
                display: flex;
                gap: 10px;
                min-width: 0;
            }}

            .copy-cell span {{
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}

            .copy-btn {{
                border: 1px solid #c7ead8;
                border-radius: 6px;
                background: var(--green-50);
                color: var(--green-800);
                cursor: pointer;
                font-size: 12px;
                font-weight: 700;
                line-height: 1;
                padding: 7px 9px;
                white-space: nowrap;
            }}

            .copy-btn:hover {{
                background: var(--green-100);
            }}

            .score-pill,
            .final-pill {{
                border-radius: 6px;
                display: inline-flex;
                min-width: 72px;
                justify-content: center;
                padding: 7px 10px;
                font-weight: 800;
            }}

            .score-pill {{
                background: #edf9f3;
                color: var(--green-700);
            }}

            .final-pill {{
                background: #dff5ea;
                color: var(--green-800);
            }}

            .details-row {{
                display: none;
            }}

            .details-row.is-open {{
                display: table-row;
            }}

            .details-row td {{
                background: #fbfefd;
                padding: 0 18px 18px;
            }}

            .details-panel {{
                border: 1px solid var(--line);
                border-radius: 8px;
                display: grid;
                gap: 14px;
                grid-template-columns: repeat(5, minmax(0, 1fr));
                padding: 16px;
            }}

            .details-label {{
                color: var(--muted);
                font-size: 12px;
                font-weight: 800;
                margin: 0 0 6px;
                text-transform: uppercase;
            }}

            .details-value {{
                color: var(--text);
                font-size: 14px;
                font-weight: 650;
                margin: 0;
                overflow-wrap: anywhere;
            }}

            @media (max-width: 900px) {{
                .candidate-shell {{
                    max-height: 620px;
                }}

                .details-panel {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>

        <script>
            const table = document.getElementById("candidate-table");
            let sortColumn = -1;
            let sortDirection = 1;

            function toggleDetails(index) {{
                const row = document.getElementById(`details-${{index}}`);
                row.classList.toggle("is-open");
            }}

            function cellValue(row, columnIndex, type) {{
                const cell = row.children[columnIndex];
                const raw = cell.dataset.value || cell.innerText || "";
                return type === "number" ? parseFloat(raw) || 0 : raw.trim().toLowerCase();
            }}

            table.querySelectorAll("th").forEach((header, columnIndex) => {{
                header.addEventListener("click", () => {{
                    const type = header.dataset.type;
                    sortDirection = sortColumn === columnIndex ? sortDirection * -1 : 1;
                    sortColumn = columnIndex;

                    const body = table.querySelector("tbody");
                    const groups = Array.from(body.querySelectorAll(".candidate-row")).map(row => {{
                        const details = row.nextElementSibling && row.nextElementSibling.classList.contains("details-row")
                            ? row.nextElementSibling
                            : null;
                        return {{ row, details }};
                    }});

                    groups.sort((a, b) => {{
                        const av = cellValue(a.row, columnIndex, type);
                        const bv = cellValue(b.row, columnIndex, type);
                        if (av < bv) return -1 * sortDirection;
                        if (av > bv) return 1 * sortDirection;
                        return 0;
                    }});

                    groups.forEach(group => {{
                        body.appendChild(group.row);
                        if (group.details) body.appendChild(group.details);
                    }});
                }});
            }});

            async function copyText(value) {{
                if (navigator.clipboard && window.isSecureContext) {{
                    await navigator.clipboard.writeText(value);
                    return;
                }}

                const textArea = document.createElement("textarea");
                textArea.value = value;
                textArea.style.position = "fixed";
                textArea.style.left = "-9999px";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand("copy");
                textArea.remove();
            }}

            document.querySelectorAll(".copy-btn").forEach(button => {{
                button.addEventListener("click", async () => {{
                    const value = JSON.parse(button.dataset.copy || '""');
                    await copyText(value);
                    const original = button.innerText;
                    button.innerText = "Copied";
                    window.setTimeout(() => button.innerText = original, 1200);
                }});
            }});
        </script>
        """,
        height=760,
        scrolling=False,
    )

def get_resume_count():

    if not os.path.exists(
        "candidate.db"
    ):
        return 0

    try:

        conn = sqlite3.connect(
            "candidate.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM candidates"
        )

        count = cursor.fetchone()[0]

        conn.close()

        return count

    except:

        return 0

st.sidebar.write(
    f"📄 Total Resumes: {get_resume_count()}"
)

if st.sidebar.button(
    "Update Resume Database"
):

    with st.spinner(
        "Updating..."
    ):

        result = subprocess.run(
            [
                sys.executable,
                "update_index.py"
            ],
            cwd=os.getcwd(),
            capture_output=True,
            text=True
        )

    st.write(
        f"Return Code: {result.returncode}"
    )

    if result.stdout:

        st.code(
            result.stdout
        )

    if result.stderr:

        st.error(
            result.stderr
        )

    new_count = get_resume_count()
    
    st.write(
    "Count after update:",
    new_count
)

    st.success(
        f"Database Updated\n\nCurrent Count: {new_count}"
    )

    # st.rerun()

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

st.title("🔍 Recruiter AI")

jd = st.text_area("Paste Job Description", height=250)
required_skills = []

if jd:
    skill_status = analyze_jd_skills(jd)

    st.markdown("##### JD Skills")

    if skill_status["known"]:
        known_skills_html = " ".join(
            f"<span style='display:inline-flex;margin:0 8px 8px 0;padding:7px 10px;border-radius:6px;background:#e7f8ef;color:#2f6f5d;font-weight:700;border:1px solid #c7ead8;'>{safe_text(skill)}</span>"
            for skill in skill_status["known"]
        )

        st.markdown(
            f"Available in skills.json<br>{known_skills_html}",
            unsafe_allow_html=True
        )

    else:
        st.caption("No skills from skills.json were found in this JD.")

    if skill_status["unknown"]:
        unknown_skills_html = " ".join(
            f"<span style='display:inline-flex;margin:0 8px 8px 0;padding:7px 10px;border-radius:6px;background:#fff8e6;color:#8a5a16;font-weight:700;border:1px solid #f1dfac;'>{safe_text(skill)}</span>"
            for skill in skill_status["unknown"]
        )

        st.markdown(
            f"New skills found in JD, not in skills.json<br>{unknown_skills_html}",
            unsafe_allow_html=True
        )

        skills_to_add = st.multiselect(
            "Select new skills to add to skills.json",
            skill_status["unknown"]
        )

        if st.button("Add Selected Skills"):

            added_skills = add_skills_to_json(skills_to_add)

            if added_skills:
                st.success(
                    "Added to skills.json: " + ", ".join(added_skills)
                )
                st.rerun()

            else:
                st.info("No new skills were added.")

    else:
        st.caption("No new skills found outside skills.json.")

    if skill_status["all"]:
        required_skills = st.multiselect(
            "Required skills candidate must have",
            skill_status["all"]
        )

if st.button("Search Candidates"):
    if jd:
        results = search_candidates(jd)

        if required_skills:
            required_skill_set = {
                skill.lower()
                for skill in required_skills
            }

            results = [
                candidate
                for candidate in results
                if required_skill_set.issubset(
                    {
                        skill.lower()
                        for skill in candidate.get("matched_skills", [])
                    }
                )
            ]

        if results:
            if required_skills:
                st.caption(
                    "Showing candidates with required skills: "
                    + ", ".join(required_skills)
                )

            render_candidate_table(results)
            st.stop()

        else:
            if required_skills:
                st.info(
                    "No candidates found with all required skills: "
                    + ", ".join(required_skills)
                )

            else:
                st.info("No candidates found.")

            st.stop()

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
