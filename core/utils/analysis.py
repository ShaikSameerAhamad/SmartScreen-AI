# core/utils/analysis.py  – LIGHT‑WEIGHT EDITION
# ------------------------------------------------
import re, os, io
import spacy
import pytesseract
import docx
import pdfplumber
import textstat
import language_tool_python
from PIL import Image
from spacy.matcher import PhraseMatcher
from pdf2image import convert_from_bytes

# lightweight ML
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .llm_handler import generate_llm_suggestions, generate_interview_questions

# ---------- CONSTANT CONFIG ----------
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\91944\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"

# ---------- LIGHT NLP MODE ----------
nlp = spacy.load("en_core_web_sm")          # ~50 MB model
tool = language_tool_python.LanguageTool("en-US")
_tfidf = TfidfVectorizer(stop_words="english")  # shared TF‑IDF instance

# ---------- STATIC DATA ----------
SKILL_CATEGORIES = {
    "Programming Languages": ['python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'go', 'ruby', 'swift', 'kotlin'],
    "Web Frameworks": ['django', 'flask', 'fastapi', 'spring boot', 'nodejs', 'express.js', 'react', 'angular', 'vue', 'svelte', 'next.js'],
    "Databases": ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'sqlite', 'nosql'],
    "Cloud & DevOps": ['aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'helm',
                       'git', 'github', 'gitlab', 'ci/cd', 'jenkins'],
    "Data Science & ML": ['data analysis', 'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'power bi', 'tableau',
                          'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn'],
    "NLP": ['nlp', 'natural language processing', 'spacy', 'nltk', 'hugging face', 'transformers'],
    "General Tools & Methodologies": ['agile', 'scrum', 'jira', 'confluence', 'project management', 'rest api',
                                      'graphql', 'soap', 'microservices', 'linux', 'bash', 'xml']
}
SECTION_PATTERNS = {
    "experience": ["experience", "work experience", "professional experience", "employment history"],
    "projects": ["projects", "academic projects", "personal projects"],
    "achievements": ["achievements", "awards", "honors"],
    "certifications": ["certifications", "licenses"],
    "education": ["education", "academic background", "qualifications"]
}

# ---------- HELPER FUNCTIONS ----------
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def normalize_resume_text(text: str) -> str:
    corrections = {
        "c sharp": "c#", "cpp": "c++", "c plus plus": "c++",
        "springboot": "spring boot", "spring-boot": "spring boot",
        "node.js": "nodejs", "node js": "nodejs",
        "expressjs": "express.js", "express": "express.js", "nextjs": "next.js",
        "no sql": "nosql", "no-sql": "nosql",
        "google cloud platform": "google cloud",
        "ci cd": "ci/cd", "ci-cd": "ci/cd",
        "git hub": "github", "git lab": "gitlab",
        "scikit learn": "scikit-learn", "scikit": "scikit-learn",
        "py torch": "pytorch", "powerbi": "power bi",
        "deep-learning": "deep learning", "machine-learning": "machine learning",
        "huggingface": "hugging face", "natural lang processing": "natural language processing",
        "restapi": "rest api", "rest-api": "rest api", "micro services": "microservices"
    }
    for wrong, right in corrections.items():
        text = re.sub(rf"\b{re.escape(wrong)}\b", right, text, flags=re.IGNORECASE)
    return text


def extract_text(uploaded_file):
    uploaded_file.seek(0)
    filename = uploaded_file.name
    _, ext = os.path.splitext(filename.lower())
    data = uploaded_file.read()
    text = ""
    try:
        if ext == ".pdf":
            if not data.strip():
                raise ValueError("Empty PDF")
            images = convert_from_bytes(data, dpi=300, poppler_path=POPPLER_PATH)
            for img in images:
                text += pytesseract.image_to_string(img, config="--psm 6") + "\n"
        elif ext == ".docx":
            doc = docx.Document(io.BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs)
        elif ext == ".txt":
            text = data.decode("utf-8")
        elif ext in [".jpg", ".jpeg", ".png", ".tiff"]:
            text = pytesseract.image_to_string(Image.open(io.BytesIO(data))) + "\n"
    except Exception as e:
        print("Extract‑text error:", e)
        return ""
    return clean_text(text)


# ---------- LIGHTWEIGHT NLP UTILITIES ----------
def extract_keywords(text: str, top_n: int = 20):
    """TF-IDF keyword extraction (no BERT)."""
    tfidf = _tfidf.fit([text])
    scores = zip(tfidf.get_feature_names_out(), tfidf.idf_)
    best = sorted(scores, key=lambda x: x[1])[:top_n]
    return [w for w, _ in best]


def semantic_match(required, resume, threshold=0.35):
    """spaCy phrase match + TF‑IDF cosine similarity."""
    matched_spacy = set()
    matcher = PhraseMatcher(nlp.vocab, attr="ORTH")
    matcher.add("SkillMatch", [nlp.make_doc(s) for s in required])
    doc = nlp(resume.lower())
    matched_spacy |= {doc[s:e].text.lower() for _, s, e in matcher(doc)}

    remaining = [s for s in required if s.lower() not in matched_spacy]
    matched_tfidf = []
    if remaining:
        matrix = _tfidf.fit_transform([resume] + remaining)
        sims = cosine_similarity(matrix[0:1], matrix[1:])[0]
        matched_tfidf = [
            remaining[i].lower() for i, sim in enumerate(sims) if sim >= threshold
        ]

    matched = list(matched_spacy | set(matched_tfidf))
    missing = [s for s in required if s.lower() not in matched]
    return matched, missing


def extract_sections(text):
    sections, lines = {}, [l.strip() for l in text.split("\n") if l.strip()]
    block = "\n".join(lines)
    for key, patterns in SECTION_PATTERNS.items():
        for p in patterns:
            m = re.search(rf"{p}.*?(?=\n[A-Z][a-z\s]{{1,20}}\n|$)", block,
                          re.I | re.S)
            if m:
                sections[key] = m.group().strip()
                break
        sections.setdefault(key, "")
    return sections


def classify_experience_level(sections):
    text = (sections.get("experience", "") + " " +
            sections.get("projects", "")).lower()
    yrs = re.findall(r"\b(\d+)\s*(?:years?|yrs?)\b", text)
    yrs = max(map(int, yrs)) if yrs else 0
    if "intern" in text or yrs == 0:
        return "Fresher"
    if yrs <= 2:
        return "Intermediate"
    return "Professional"


def grade_resume(text):
    feedback = {}
    score = 0
    word_count = len(text.split())
    text_lower = text.lower()

    if word_count < 200:
        score += 5
        feedback['length'] = f"Resume is very brief ({word_count} words). Consider expanding."
    elif 400 <= word_count <= 800:
        score += 25
        feedback['length'] = f"Good length ({word_count} words)."
    else:
        score += 15
        feedback['length'] = f"Consider adjusting length ({word_count} words)."

    grammar_issues = len(tool.check(text))
    readability = textstat.flesch_reading_ease(text)
    feedback['grammar'] = f"{grammar_issues} grammar issues found."
    feedback['readability'] = f"Readability score is {readability:.2f}."

    if re.search(r"references available", text_lower):
        feedback['red_flag'] = "Avoid generic phrases like 'References available upon request'."

    sections_found = [s for s in ['experience', 'skills', 'education', 'projects'] if re.search(r'\b' + s + r'\b', text_lower)]
    if len(sections_found) >= 2:
        score += 25
    feedback['sections'] = f"Found {len(sections_found)} key sections."

    strong_verbs = ['developed', 'managed', 'optimized', 'created', 'built','implemented', 'achieved', 'led', 'launched']
    verb_count = sum(1 for v in strong_verbs if re.search(r'\b' + v + r'\b', text_lower))
    score += min(verb_count, 5) * 5
    feedback['action_verbs'] = f"{verb_count} strong action verbs used."

    metrics = re.findall(r'(\d+%|\$\d+|\d+x|\d+\s+(?:users|clients|projects|downloads|sales))', text_lower)
    score += min(len(metrics), 3) * 5
    feedback['metrics'] = f"{len(metrics)} quantifiable metrics found."

    return min(score, 100), feedback


# ---------- MAIN ANALYSIS PIPELINE ----------
def perform_full_analysis(resume_text, job_skills_text,
                          full_jd_text, job_title="Custom Role"):
    resume_text = normalize_resume_text(resume_text)
    if not resume_text or not job_skills_text:
        return {"error": "Missing input."}

    jd_keywords = extract_keywords(normalize_resume_text(job_skills_text))
    matched, missing = semantic_match(jd_keywords, resume_text)

    suggestions = generate_llm_suggestions(resume_text, job_title,
                                           job_skills_text, full_jd_text)
    grade, feedback = grade_resume(resume_text)
    match_score = round(len(matched) / len(jd_keywords) * 100, 2) if jd_keywords else 0
    final_score = round(0.6 * match_score + 0.4 * grade, 2)

    # Category bucket
    cat = {}
    skill_to_cat = {s.lower(): c for c, lst in SKILL_CATEGORIES.items() for s in lst}
    for skill in set(matched + missing):
        cat.setdefault(skill_to_cat.get(skill, "Uncategorized"),
                       {"matched": [], "missing": []})
        (cat[skill_to_cat.get(skill, "Uncategorized")]
         ["matched" if skill in matched else "missing"].append(skill))

    # Stats & extras
    sections = extract_sections(resume_text)
    exp_lvl = classify_experience_level(sections)
    interview_qs = generate_interview_questions(
        resume_text, exp_lvl, sections.get("projects", ""),
        ", ".join(matched))

    return {
        "match_score": match_score,
        "missing_skills": missing,
        "matched_skills": matched,
        "ai_suggestions": suggestions,
        "resume_grade": grade,
        "grading_feedback": feedback,
        "final_score": final_score,
        "categorized_analysis": cat,
        "summary_stats": {
            "total_required_skills": len(jd_keywords),
            "total_matched_skills": len(matched),
            "matching_ratio": f"{len(matched)}/{len(jd_keywords)}",
            "percent": match_score,
        },
        "experience_level": exp_lvl,
        "extracted_sections": sections,
        "interview_questions": interview_qs,
    }
