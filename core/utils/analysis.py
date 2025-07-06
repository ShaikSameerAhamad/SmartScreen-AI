# core/utils/analysis.py

import re
import os
import io
import spacy
import pytesseract
import docx
import pdfplumber
import textstat
import language_tool_python
from PIL import Image
from spacy.matcher import PhraseMatcher
from pdf2image import convert_from_bytes
from sentence_transformers import SentenceTransformer, util
from keybert import KeyBERT
from .llm_handler import generate_llm_suggestions

# --- Configuration ---
pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\91944\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'
POPPLER_PATH = r'C:\\poppler-24.08.0\\Library\\bin'
nlp = spacy.load("en_core_web_lg")
tool = language_tool_python.LanguageTool('en-US')
kw_model = KeyBERT()
bert_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- SKILLS ORGANIZED BY CATEGORY ---
SKILL_CATEGORIES = {
    "Programming Languages": ['python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'go', 'ruby', 'swift', 'kotlin'],
    "Web Frameworks": ['django', 'flask', 'fastapi', 'spring boot', 'ruby on rails', 'nodejs', 'express.js', 'react', 'angular', 'vue', 'svelte', 'next.js'],
    "Databases": ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'sqlite', 'nosql'],
    "Cloud & DevOps": ['aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'helm', 'git', 'github', 'gitlab', 'ci/cd', 'jenkins'],
    "Data Science & ML": ['data analysis', 'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'power bi', 'tableau', 'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn'],
    "NLP": ['nlp', 'natural language processing', 'spacy', 'nltk', 'hugging face', 'transformers'],
    "General Tools & Methodologies": ['agile', 'scrum', 'jira', 'confluence', 'project management', 'rest api', 'graphql', 'soap', 'microservices', 'linux', 'bash', 'xml']
}

# --- HELPER FUNCTIONS ---
def clean_text(text):
    if not text: return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'[^\w\s@.-]', '', text)
    return text.strip()

def extract_text(uploaded_file):
    uploaded_file.seek(0)
    filename = uploaded_file.name
    _, extension = os.path.splitext(filename)
    extension = extension.lower()
    file_content = uploaded_file.read()
    text = ""
    try:
        if extension == '.pdf':
            if not file_content.strip():
                raise ValueError("Uploaded PDF file is empty!")
            images = convert_from_bytes(file_content, dpi=300, poppler_path=POPPLER_PATH)
            for img in images:
                text += pytesseract.image_to_string(img, config='--psm 6')
        elif extension == '.docx':
            doc = docx.Document(io.BytesIO(file_content))
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif extension == '.txt':
            text = file_content.decode('utf-8')
        elif extension in ['.jpg', '.jpeg', '.png', '.tiff']:
            image = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(image)
    except Exception as e:
        print(f"ERROR during text extraction for {filename}: {e}")
        return ""
    return clean_text(text)

def extract_keywords(text):
    keywords = kw_model.extract_keywords(text, top_n=20)
    return [kw for kw, _ in keywords]

def semantic_match(required_skills, resume_text):
    matched, missing = [], []

    if not required_skills or not resume_text:
        return matched, required_skills

    resume_lower = resume_text.lower()

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in required_skills]
    matcher.add("SkillMatch", patterns)
    doc = nlp(resume_lower)
    matches = matcher(doc)

    # ✅ FIXED: Safely extract matched text
    matched_spacy = {doc[start:end].text.lower() for _, start, end in matches}

    remaining_skills = [s for s in required_skills if s.lower() not in matched_spacy]

    # Semantic similarity using BERT
    matched_bert = []
    if remaining_skills:
        skill_embeddings = bert_model.encode(remaining_skills, convert_to_tensor=True)
        resume_embedding = bert_model.encode(resume_text, convert_to_tensor=True)
        similarities = util.cos_sim(resume_embedding, skill_embeddings)[0]

        for i, score in enumerate(similarities):
            if score >= 0.6:
                matched_bert.append(remaining_skills[i].lower())

    # Combine and deduplicate
    matched = list(set(matched_bert).union(matched_spacy))
    missing = [s for s in required_skills if s.lower() not in matched]

    return matched, missing


def extract_section(title, text):
    pattern = rf"{title}.*?(?=\n[A-Z])"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group() if match else ""

def categorize_skills(matched_skills):
    categorized = {cat: [] for cat in SKILL_CATEGORIES}
    for skill in matched_skills:
        for category, skill_list in SKILL_CATEGORIES.items():
            if skill.lower() in skill_list:
                categorized[category].append(skill)
    return {k: v for k, v in categorized.items() if v}

def grade_resume(text):
    feedback = {}
    score = 0
    word_count = len(text.split())
    text_lower = text.lower()

    if word_count < 200: score += 5; feedback['length'] = f"Resume is very brief ({word_count} words). Consider expanding."
    elif 400 <= word_count <= 800: score += 25; feedback['length'] = f"Good length ({word_count} words)."
    else: score += 15; feedback['length'] = f"Consider adjusting length ({word_count} words)."

    grammar_issues = len(tool.check(text))
    readability = textstat.flesch_reading_ease(text)
    feedback['grammar'] = f"{grammar_issues} grammar issues found."
    feedback['readability'] = f"Readability score is {readability:.2f}."

    if re.search(r"references available", text_lower):
        feedback['red_flag'] = "Avoid generic phrases like 'References available upon request'."

    sections_found = [s for s in ['experience', 'skills', 'education', 'projects'] if re.search(r'\b' + s + r'\b', text_lower)]
    if len(sections_found) >= 2: score += 25
    feedback['sections'] = f"Found {len(sections_found)} key sections."

    strong_verbs = ['developed', 'managed', 'optimized', 'created', 'built', 'implemented', 'achieved', 'led', 'launched']
    verb_count = sum(1 for verb in strong_verbs if re.search(r'\b' + verb + r'\b', text_lower))
    score += min(verb_count, 5) * 5
    feedback['action_verbs'] = f"{verb_count} strong action verbs used."

    metrics = re.findall(r'(\d+%|\$\d+|\d+x|\d+\s+(?:users|clients|projects|downloads|sales))', text_lower)
    score += min(len(metrics), 3) * 5
    feedback['metrics'] = f"{len(metrics)} quantifiable metrics found."

    return min(score, 100), feedback

def perform_full_analysis(resume_text, job_skills_text, full_jd_text):
    if not resume_text or not job_skills_text:
        return {
            "match_score": 0,
            "missing_skills": [],
            "matched_skills": [],
            "ai_suggestions": "Missing input.",
            "resume_grade": 0,
            "grading_feedback": {"error": "Invalid input."},
            "final_score": 0,
            "categorized_analysis": {}
        }

    jd_keywords = extract_keywords(job_skills_text)
    matched_skills, missing_skills = semantic_match(jd_keywords, resume_text)
    suggestions = generate_llm_suggestions(resume_text, full_jd_text)
    grade, feedback = grade_resume(resume_text)
    match_score = round(len(matched_skills) / len(jd_keywords) * 100, 2) if jd_keywords else 0
    final_score = round((0.6 * match_score) + (0.4 * grade), 2)

    # ✅ New logic for categorizing skills
    categorized = {}
    matched_set = set(s.lower() for s in matched_skills)
    missing_set = set(s.lower() for s in missing_skills)

    for category, skill_list in SKILL_CATEGORIES.items():
        matched = [skill for skill in skill_list if skill.lower() in matched_set]
        missing = [skill for skill in skill_list if skill.lower() in missing_set]
        total_required = len(skill_list)
        matched_count = len(matched)
        score = round((matched_count / total_required) * 100, 2) if total_required else 0
       
        if matched or missing:
            categorized[category] = {
                "matched": matched,
                "missing": missing,
                "matched_count": matched_count,
                "total_required": total_required,
                "score": score
            }

    return {
        "match_score": match_score,
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
        "ai_suggestions": suggestions,
        "resume_grade": grade,
        "grading_feedback": feedback,
        "final_score": final_score,
        "categorized_analysis": categorized  # ✅ Now included
    }
