# core/utils/analysis.py
import re
import os
import spacy
import pytesseract
from PIL import Image
from spacy.matcher import PhraseMatcher
from pdf2image import convert_from_bytes
import io
import docx
import pdfplumber
from .llm_handler import generate_llm_suggestions

# --- Configuration ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\91944\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler-24.08.0\Library\bin'
nlp = spacy.load("en_core_web_lg")

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
            print("[INFO] Attempting direct OCR on PDF using pdf2image")
            # Make sure we pass actual bytes
            if not file_content.strip():
                raise ValueError("Uploaded PDF file is empty!")
            # Convert PDF to images (requires poppler)
            images = convert_from_bytes(
                file_content,
                dpi=300,
                poppler_path=r'C:\poppler-24.08.0\Library\bin'  # Update to match your actual path
            )
            for img in images:
                ocr_text = pytesseract.image_to_string(img)
                text += ocr_text
        elif extension == '.docx':
            doc = docx.Document(io.BytesIO(file_content))
            for para in doc.paragraphs: text += para.text + "\n"
        elif extension == '.txt':
            text = file_content.decode('utf-8')
        elif extension in ['.jpg', '.jpeg', '.png', '.tiff']:
            image = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(image)
    except Exception as e:
        print(f"ERROR during text extraction for {filename}: {e}")
        return ""
    return clean_text(text)

def extract_categorized_skills(text):
    categorized_skills = {category: [] for category in SKILL_CATEGORIES}
    all_skills_flat = [skill for skills in SKILL_CATEGORIES.values() for skill in skills]
    skill_to_category_map = {skill: category for category, skills in SKILL_CATEGORIES.items() for skill in skills}
    matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
    patterns = [nlp.make_doc(skill) for skill in all_skills_flat]
    matcher.add("SKILL_MATCHER", patterns)
    doc = nlp(text.lower())
    matches = matcher(doc)
    found_skills = set(span.text for _, start, end in matches for span in [doc[start:end]])
    for skill in found_skills:
        if category := skill_to_category_map.get(skill):
            categorized_skills[category].append(skill)
    return {cat: skills for cat, skills in categorized_skills.items() if skills}

def grade_resume(text):
    feedback = {}
    score = 0
    word_count = len(text.split())
    if word_count < 200: score += 5; feedback['length'] = f"Resume is very brief ({word_count} words). Consider expanding."
    elif 400 <= word_count <= 800: score += 25; feedback['length'] = f"Good length ({word_count} words)."
    else: score += 15; feedback['length'] = f"Consider adjusting length ({word_count} words)."
    sections_found = [s for s in ['experience', 'skills', 'education', 'projects'] if re.search(r'\b' + s + r'\b', text, re.IGNORECASE)]
    if len(sections_found) >= 2: score += 25
    feedback['sections'] = f"Found {len(sections_found)} key sections."
    action_verbs = ['developed', 'led', 'managed', 'created', 'implemented', 'designed', 'optimized', 'analyzed', 'built']
    verb_count = sum(1 for verb in action_verbs if verb in text.lower())
    if verb_count >= 3: score += 25; feedback['action_verbs'] = f"Good use of action verbs ({verb_count} found)."
    else: score += 10; feedback['action_verbs'] = "Use more powerful action verbs."
    quantifiable_count = len(re.findall(r'(\d+%|\d+\s*percent|\$\d+|\d+x\b)', text.lower()))
    if quantifiable_count >= 1: score += 25; feedback['quantifiable_results'] = f"Excellent! Found {quantifiable_count} quantifiable result(s)."
    else: score += 10; feedback['quantifiable_results'] = "Add quantifiable results to show impact."
    return min(score, 100), feedback

# --- MAIN ANALYSIS FUNCTION ---
def perform_full_analysis(resume_text, job_skills_text, full_jd_text):
    if not resume_text or not resume_text.strip():
        return {"match_score": 0, "missing_skills": [], "matched_skills": [], "ai_suggestions": "Could not extract text from the resume.", "resume_grade": 0, "grading_feedback": {"error": "Text extraction failed."}, "categorized_analysis": {}}
    if not job_skills_text or not job_skills_text.strip():
        return {"match_score": 0, "missing_skills": [], "matched_skills": [], "ai_suggestions": "Job description was not provided.", "resume_grade": 0, "grading_feedback": {"error": "Missing job description."}, "categorized_analysis": {}}
    
    required_skills_by_cat = extract_categorized_skills(job_skills_text)
    resume_skills_by_cat = extract_categorized_skills(resume_text)
    categorical_analysis = {}
    all_required_skills = set()
    all_matched_skills = set()
    for category, req_skills in required_skills_by_cat.items():
        req_set = set(req_skills)
        res_set = set(resume_skills_by_cat.get(category, []))
        matched = req_set.intersection(res_set)
        missing = req_set.difference(res_set)
        all_required_skills.update(req_set)
        all_matched_skills.update(matched)
        score = (len(matched) / len(req_set)) * 100 if req_set else 0
        if req_set:
            categorical_analysis[category] = {"score": round(score), "matched": list(matched), "missing": list(missing)}
    overall_score = (len(all_matched_skills) / len(all_required_skills)) * 100 if all_required_skills else 0
    suggestions = generate_llm_suggestions(resume_text, full_jd_text)
    grade, grading_feedback = grade_resume(resume_text)
    return {
        "match_score": round(overall_score, 2),
        "missing_skills": list(all_required_skills.difference(all_matched_skills)),
        "matched_skills": list(all_matched_skills),
        "ai_suggestions": suggestions,
        "resume_grade": grade,
        "grading_feedback": grading_feedback,
        "categorized_analysis": categorical_analysis
    }