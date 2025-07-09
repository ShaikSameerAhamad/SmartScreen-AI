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
from .llm_handler import generate_llm_suggestions, generate_interview_questions

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
    "Web Frameworks": ['django', 'flask', 'fastapi', 'spring boot', 'nodejs', 'express.js', 'react', 'angular', 'vue', 'svelte', 'next.js'],
    "Databases": ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'sqlite', 'nosql'],
    "Cloud & DevOps": ['aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'helm', 'git', 'github', 'gitlab', 'ci/cd', 'jenkins'],
    "Data Science & ML": ['data analysis', 'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'power bi', 'tableau', 'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn'],
    "NLP": ['nlp', 'natural language processing', 'spacy', 'nltk', 'hugging face', 'transformers'],
    "General Tools & Methodologies": ['agile', 'scrum', 'jira', 'confluence', 'project management', 'rest api', 'graphql', 'soap', 'microservices', 'linux', 'bash', 'xml']
}
SECTION_PATTERNS = {
    "experience": ["experience", "work experience", "professional experience", "employment history"],
    "projects": ["projects", "academic projects", "personal projects"],
    "achievements": ["achievements", "awards", "honors"],
    "certifications": ["certifications", "licenses"],
    "education": ["education", "academic background", "qualifications"]
}


# --- HELPER FUNCTIONS ---
def clean_text(text):
    if not text:
        return ""
    text = text.replace('\r', '\n')  # Normalize line breaks
    text = re.sub(r'\n+', '\n', text)  # Collapse multiple newlines
    return text.strip()

def normalize_resume_text(text):
    corrections = {
        # Programming
        "c sharp": "c#",
        "cpp": "c++",
        "c plus plus": "c++",

        # Web Frameworks
        "springboot": "spring boot",
        "spring-boot": "spring boot",
        "node.js": "nodejs",
        "node js": "nodejs",
        "expressjs": "express.js",
        "express": "express.js",
        "nextjs": "next.js",

        # Databases
        "no sql": "nosql",
        "no-sql": "nosql",

        # Cloud & DevOps
        "google cloud platform": "google cloud",
        "ci cd": "ci/cd",
        "ci-cd": "ci/cd",
        "git hub": "github",
        "git lab": "gitlab",

        # Data Science & ML
        "scikit learn": "scikit-learn",
        "scikit": "scikit-learn",
        "learn": "",
        "py torch": "pytorch",
        "powerbi": "power bi",
        "deep-learning": "deep learning",
        "machine-learning": "machine learning",

        # NLP
        "huggingface": "hugging face",
        "natural lang processing": "natural language processing",

        # Tools
        "restapi": "rest api",
        "rest-api": "rest api",
        "micro services": "microservices"
    }

    for wrong, right in corrections.items():
        text = re.sub(rf"\b{re.escape(wrong)}\b", right, text, flags=re.IGNORECASE)
    return text


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
                text += pytesseract.image_to_string(img, config='--psm 6') + '\n'
        elif extension == '.docx':
            doc = docx.Document(io.BytesIO(file_content))
            for para in doc.paragraphs:
                text += para.text + '\n'
        elif extension == '.txt':
            text = file_content.decode('utf-8')
        elif extension in ['.jpg', '.jpeg', '.png', '.tiff']:
            image = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(image) + '\n'
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
    matcher = PhraseMatcher(nlp.vocab, attr="ORTH")
    patterns = [nlp.make_doc(skill) for skill in required_skills]
    matcher.add("SkillMatch", patterns)
    doc = nlp(resume_lower)
    matches = matcher(doc)
    matched_spacy = {doc[start:end].text.lower() for _, start, end in matches}

    matched_spacy = matched_spacy.intersection(set(s.lower() for s in required_skills))
    remaining_skills = [s for s in required_skills if s.lower() not in matched_spacy]

    matched_bert = []
    if remaining_skills:
        skill_embeddings = bert_model.encode(remaining_skills, convert_to_tensor=True)
        resume_embedding = bert_model.encode(resume_text, convert_to_tensor=True)
        similarities = util.cos_sim(resume_embedding, skill_embeddings)[0]

        for i, score in enumerate(similarities):
            if score >= 0.6:
                matched_bert.append(remaining_skills[i].lower())

    matched = list(set(matched_bert).union(matched_spacy))
    missing = [s for s in required_skills if s.lower() not in matched]

    return matched, missing

def extract_sections(text):
    sections = {}
    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    text_block = "\n".join(lines)

    for section_key, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            match = re.search(rf"{pattern}.*?(?=\n[A-Z][a-z\s]{{1,20}}\n|$)", text_block, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section_key] = match.group().strip()
                break
        if section_key not in sections:
            sections[section_key] = ""
    return sections

def classify_experience_level(sections):
    """
    More accurate classifier based on experience text + keywords.
    """
    text_all = " ".join(sections.values()).lower()
    exp_text = sections.get('experience', '').lower()
    projects_text = sections.get('projects', '').lower()

    score = {"Fresher": 0, "Intermediate": 0, "Professional": 0}

    # Detect internship / freshers
    if 'intern' in exp_text or 'intern' in projects_text:
        score['Fresher'] += 2
    if any(x in text_all for x in ['student', 'pursuing', 'b.tech', 'bachelor']):
        score['Fresher'] += 2
    if re.search(r'\b(0|0-1|less than 1)\+?\s*(years|yrs)\b', exp_text):
        score['Fresher'] += 2

    # Intermediate signals
    if any(x in exp_text for x in ['developed', 'implemented', 'enhanced']) and 'years' not in exp_text:
        score['Intermediate'] += 1
    if re.search(r'\b(1|1-2|2)\+?\s*(years|yrs)\b', exp_text):
        score['Intermediate'] += 2

    # Professional signals
    if re.search(r'\b(3|4|5|\d{2,})\+?\s*(years|yrs)\b', exp_text):
        score['Professional'] += 3
    if any(x in exp_text for x in ['led', 'managed', 'deployed', 'architected', 'mentored']):
        score['Professional'] += 1

    # Final decision
    if score['Professional'] >= 3:
        return "Professional"
    elif score['Intermediate'] >= 2:
        return "Intermediate"
    elif score['Fresher'] >= 2:
        return "Fresher"
    else:
        return "Fresher"  # Default if unsure


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

def perform_full_analysis(resume_text, job_skills_text, full_jd_text, job_title="Custom Role"):
    resume_text = normalize_resume_text(resume_text)
    if not resume_text or not job_skills_text:
        return {
            "match_score": 0,
            "missing_skills": [],
            "matched_skills": [],
            "ai_suggestions": "Missing input.",
            "resume_grade": 0,
            "grading_feedback": {"error": "Invalid input."},
            "final_score": 0,
            "categorized_analysis": {},
            "summary_stats": {
                "total_required_skills": 0,
                "total_matched_skills": 0,
                "matching_ratio": "0/0",
                "percent": 0
            },
            "experience_level": "Unknown",
            "extracted_sections": {},
            "interview_questions": "No questions generated. Try re-analyzing with a more detailed resume."
        }

    normalized_jd_text = normalize_resume_text(job_skills_text)
    jd_keywords = extract_keywords(normalized_jd_text)

    matched_skills, missing_skills = semantic_match(jd_keywords, resume_text)
    suggestions = generate_llm_suggestions(resume_text, job_title, job_skills_text, full_jd_text)
    grade, feedback = grade_resume(resume_text)
    match_score = round(len(matched_skills) / len(jd_keywords) * 100, 2) if jd_keywords else 0
    final_score = round((0.6 * match_score) + (0.4 * grade), 2)

    categorized = {}
    matched_set = set(s.lower() for s in matched_skills)
    missing_set = set(s.lower() for s in missing_skills)

    skill_to_category = {}
    for category, skills in SKILL_CATEGORIES.items():
        for s in skills:
            skill_to_category[s.lower()] = category

    bucket = {}
    for skill in matched_set.union(missing_set):
        category = skill_to_category.get(skill)
        if not category:
            continue
        if category not in bucket:
            bucket[category] = {"matched": [], "missing": [], "total_required": 0}

        if skill in matched_set:
            bucket[category]["matched"].append(skill)
        elif skill in missing_set:
            bucket[category]["missing"].append(skill)

    for category, data in bucket.items():
        total = len(data["matched"]) + len(data["missing"])
        score = round((len(data["matched"]) / total) * 100, 2) if total else 0
        categorized[category] = {
            "matched": data["matched"],
            "missing": data["missing"],
            "matched_count": len(data["matched"]),
            "total_required": total,
            "score": score
        }

    remaining_uncategorized_skills = [
        s for s in missing_skills
        if s.lower() not in skill_to_category
    ]

    if remaining_uncategorized_skills:
        categorized["Uncategorized"] = {
            "matched": [],
            "missing": remaining_uncategorized_skills,
            "matched_count": 0,
            "total_required": len(remaining_uncategorized_skills),
            "score": 0
        }

    summary_stats = {
        "total_required_skills": len(jd_keywords),
        "total_matched_skills": len(matched_skills),
        "matching_ratio": f"{len(matched_skills)}/{len(jd_keywords)}",
        "percent": match_score
    }

    # --- Section Extraction ---
    extracted_sections = extract_sections(resume_text)

    # --- Experience Level Classification ---
    experience_level = classify_experience_level(extracted_sections)

    # --- Interview Questions Generation ---
    projects_text = extracted_sections.get("projects", "")
    skills_summary = ", ".join(matched_skills)

    interview_questions = generate_interview_questions(
        resume_text=resume_text,
        experience_level=experience_level,
        project_info=projects_text,
        skill_summary=skills_summary
    )
    
    return {
        "match_score": match_score,
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
        "ai_suggestions": suggestions,
        "resume_grade": grade,
        "grading_feedback": feedback,
        "final_score": final_score,
        "categorized_analysis": categorized,
        "summary_stats": summary_stats,
        "experience_level": experience_level,
        "extracted_sections": extracted_sections,
        "interview_questions": interview_questions
    }
