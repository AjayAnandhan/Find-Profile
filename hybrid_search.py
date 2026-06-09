"""
Hybrid search engine supporting multiple matching strategies:
- semantic: FAISS + sentence-transformers (current behavior)
- skills:   Pure keyword/skill matching (no ML model required)
- hybrid:   Combines both with configurable weights
- tfidf:    TF-IDF cosine similarity (lightweight, no model download)
"""

import os
import pickle
import re
import sqlite3

import faiss
from sentence_transformers import SentenceTransformer

from jd_parser import analyze_jd_skills, extract_experience
from scorer import experience_score


# ---------------------------------------------------------------------------
# Lazy-loaded resources
# ---------------------------------------------------------------------------
_MODEL = None
_INDEX = None
_FILENAMES = []
_TFIDF_VECTORIZER = None
_TFIDF_MATRIX = None
_TFIDF_DOC_IDS = []


def _get_model():
    """Load the sentence-transformer model only when needed."""
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _MODEL


def _load_faiss_index():
    """Load FAISS index and filename list from disk (cached)."""
    global _INDEX, _FILENAMES
    if _INDEX is None and os.path.exists("resume_index.faiss"):
        _INDEX = faiss.read_index("resume_index.faiss")
    if not _FILENAMES and os.path.exists("resume_metadata.pkl"):
        with open("resume_metadata.pkl", "rb") as f:
            _FILENAMES = pickle.load(f)
    return _INDEX, _FILENAMES


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------
def _keyword_score(jd, resume_text):
    """
    Score a resume against a JD based on keyword overlap.
    Returns a percentage 0-100.
    """
    jd_words = set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.\-]{1,}\b", jd.lower()))
    resume_words = set(
        re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.\-]{1,}\b", resume_text.lower())
    )

    # Drop very common stopwords to reduce noise
    stop = {
        "the",
        "and",
        "for",
        "with",
        "you",
        "our",
        "are",
        "will",
        "have",
        "from",
        "this",
        "that",
        "your",
        "their",
        "they",
        "them",
        "any",
        "all",
        "can",
        "who",
        "what",
        "when",
        "where",
        "why",
        "how",
        "role",
        "team",
        "company",
        "work",
        "year",
        "years",
        "etc",
    }
    jd_words -= stop

    if not jd_words:
        return 0.0

    overlap = jd_words & resume_words
    return round(len(overlap) / len(jd_words) * 100, 2)


def _skill_score(jd, resume_text):
    """
    Score a resume against a JD based on the skills detected in the JD.
    Uses the same skill analysis as the rest of the app for consistency.
    """
    jd_skills = analyze_jd_skills(jd)["all"]
    if not jd_skills:
        return 0.0

    resume_lower = resume_text.lower()
    matched = sum(1 for s in jd_skills if s.lower() in resume_lower)
    return round(matched / len(jd_skills) * 100, 2)


def _matched_missing_skills(jd, resume_text):
    """Return (matched, missing) skill lists for display."""
    jd_skills = analyze_jd_skills(jd)["all"]
    resume_lower = resume_text.lower()
    matched, missing = [], []
    for s in jd_skills:
        if s.lower() in resume_lower:
            matched.append(s)
        else:
            missing.append(s)
    return matched, missing


def _semantic_score(jd, top_k=100):
    """
    Return [(filepath, score_percent), ...] ranked by semantic similarity.
    Empty list if FAISS index is unavailable.
    """
    index, filenames = _load_faiss_index()
    if index is None or not filenames:
        return []

    model = _get_model()
    query_embedding = model.encode([jd])
    distances, indices = index.search(query_embedding, min(top_k, len(filenames)))

    results = []
    for rank, idx in enumerate(indices[0]):
        if idx == -1:
            continue
        score = round((1 / (1 + distances[0][rank])) * 100, 2)
        results.append((filenames[idx], score))
    return results


def _tfidf_search(jd, top_k=100):
    """
    Lightweight TF-IDF cosine similarity search.
    No model download; uses scikit-learn's TfidfVectorizer.
    Caches the vectorizer and matrix between calls.
    """
    global _TFIDF_VECTORIZER, _TFIDF_MATRIX, _TFIDF_DOC_IDS
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    conn = sqlite3.connect("candidate.db")
    cursor = conn.cursor()
    cursor.execute("SELECT filepath, resume_text FROM candidates")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    filepaths = [r[0] for r in rows]
    texts = [r[1] or "" for r in rows]

    # Rebuild cache if filepaths changed
    if _TFIDF_VECTORIZER is None or filepaths != _TFIDF_DOC_IDS:
        _TFIDF_VECTORIZER = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=20000,
        )
        _TFIDF_MATRIX = _TFIDF_VECTORIZER.fit_transform(texts)
        _TFIDF_DOC_IDS = filepaths

    jd_vec = _TFIDF_VECTORIZER.transform([jd])
    sims = cosine_similarity(jd_vec, _TFIDF_MATRIX).flatten()

    ranked = sorted(
        zip(filepaths, sims),
        key=lambda x: x[1],
        reverse=True,
    )[:top_k]
    return [(fp, round(float(score) * 100, 2)) for fp, score in ranked]


# ---------------------------------------------------------------------------
# Weight presets
# ---------------------------------------------------------------------------
WEIGHT_PRESETS = {
    "semantic": {"semantic": 0.70, "skill": 0.20, "experience": 0.10, "tfidf": 0.00},
    "skills": {"semantic": 0.00, "skill": 0.80, "experience": 0.20, "tfidf": 0.00},
    "hybrid": {"semantic": 0.45, "skill": 0.40, "experience": 0.10, "tfidf": 0.05},
    "tfidf": {"semantic": 0.00, "skill": 0.30, "experience": 0.10, "tfidf": 0.60},
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def search_candidates_hybrid(jd, mode="hybrid", top_k=100, custom_weights=None):
    """
    Search candidates from local DB using the selected matching mode.

    Parameters
    ----------
    jd : str
        The job description text.
    mode : str
        One of: 'semantic', 'skills', 'hybrid', 'tfidf'.
    top_k : int
        Number of candidates to consider from the semantic/TF-IDF stage.
    custom_weights : dict or None
        Optional override of weight preset.

    Returns
    -------
    list of dict
        Each dict contains name, email, phone, experience, resume, filepath,
        semantic_score, skill_score, experience_score, tfidf_score,
        final_score, matched_skills, missing_skills.
    """
    mode = (mode or "hybrid").lower()
    if mode not in WEIGHT_PRESETS:
        mode = "hybrid"

    weights = dict(WEIGHT_PRESETS[mode])
    if custom_weights:
        weights.update(custom_weights)

    jd_exp = extract_experience(jd)

    # -------- Stage 1: pick candidate pool --------
    if mode == "semantic":
        pool = _semantic_score(jd, top_k=top_k)
    elif mode == "tfidf":
        pool = _tfidf_search(jd, top_k=top_k)
    else:
        # For skills/hybrid: pull every candidate from the DB (keyword scoring
        # is cheap, so we evaluate all of them).
        pool = _all_filepaths()

    if not pool:
        return []

    # Normalize semantic / tfidf pool scores to a dict for quick lookup
    semantic_lookup = {fp: score for fp, score in pool}

    # -------- Stage 2: enrich with structured scores --------
    conn = sqlite3.connect("candidate.db")
    cursor = conn.cursor()

    results = []
    for filepath in semantic_lookup.keys():
        cursor.execute(
            """
            SELECT name, email, phone, experience, resume_text
            FROM candidates
            WHERE filepath=?
            LIMIT 1
            """,
            (filepath,),
        )
        row = cursor.fetchone()
        if not row:
            continue

        name, email, phone, experience, resume_text = row
        sem_score = semantic_lookup.get(filepath, 0.0)
        sk_score = _skill_score(jd, resume_text or "")
        exp_score = experience_score(jd_exp, experience or 0)
        tfidf_score = 0.0
        if mode == "tfidf":
            tfidf_score = sem_score  # already a tfidf % from pool
        elif mode == "hybrid":
            # Optionally compute tfidf on-demand (skipped for speed by default)

            pass
        matched, missing = _matched_missing_skills(jd, resume_text or "")

        final = round(
            sem_score * weights["semantic"]
            + sk_score * weights["skill"]
            + exp_score * weights["experience"]
            + tfidf_score * weights["tfidf"],
            2,
        )

        results.append(
            {
                "name": name,
                "email": email,
                "phone": phone,
                "experience": experience,
                "resume": os.path.basename(filepath),
                "filepath": filepath,
                "semantic_score": sem_score,
                "skill_score": sk_score,
                "experience_score": exp_score,
                "tfidf_score": tfidf_score,
                "final_score": final,
                "matched_skills": matched,
                "missing_skills": missing,
            }
        )

    conn.close()

    # For skills-only mode, if pool came from the full DB, re-rank by final.
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:top_k]


def _all_filepaths():
    """Return all candidate filepaths from the DB (used by skills/hybrid)."""
    if not os.path.exists("candidate.db"):
        return []
    conn = sqlite3.connect("candidate.db")
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM candidates")
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return [(fp, 0.0) for fp in rows]
