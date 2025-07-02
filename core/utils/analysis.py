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
    """
    Grades a resume based on a more advanced set of rules, including
    a wider range of action verbs and quantifiable metrics.
    """
    feedback = {}
    score = 0
    word_count = len(text.split())
    text_lower = text.lower()

    # Rule 1: Resume Length (unchanged)
    if word_count < 200: score += 5; feedback['length'] = f"Resume is very brief ({word_count} words). Consider expanding."
    elif 400 <= word_count <= 800: score += 25; feedback['length'] = f"Good length ({word_count} words)."
    else: score += 15; feedback['length'] = f"Consider adjusting length ({word_count} words)."

    # Rule 2: Presence of Important Sections (unchanged)
    sections_found = [s for s in ['experience', 'skills', 'education', 'projects'] if re.search(r'\b' + s + r'\b', text_lower)]
    if len(sections_found) >= 2: score += 25
    feedback['sections'] = f"Found {len(sections_found)} key sections."

    # Rule 3: Use of Action Verbs (ENHANCED)
    strong_action_verbs = [
        'achieved', 'accelerated', 'accomplished', 'architected', 'automated', 'built', 'conceived',
        'created', 'designed', 'developed', 'directed', 'engineered', 'founded', 'generated',
        'implemented', 'improved', 'increased', 'initiated', 'innovated', 'instituted', 'launched',
        'led', 'managed', 'negotiated', 'optimized', 'overhauled', 'pioneered', 'produced',
        'reduced', 're-engineered', 'resolved', 'revamped', 'spearheaded', 'streamlined', 'strengthened'
    ]
    verb_count = sum(1 for verb in strong_action_verbs if re.search(r'\b' + verb + r'\b', text_lower))
    if verb_count >= 5:
        score += 25
        feedback['action_verbs'] = f"Excellent! Found {verb_count} strong action verbs."
    elif verb_count >= 2:
        score += 15
        feedback['action_verbs'] = f"Good start with {verb_count} action verbs. Try to add more to describe your impact."
    else:
        score += 5
        feedback['action_verbs'] = "Weak use of action verbs. Use verbs like 'developed', 'managed', 'optimized' to show initiative."

    # Rule 4: Use of Quantifiable Results (ENHANCED)
    # This regex looks for percentages, dollar amounts, 'x' multipliers (like 10x), and numbers followed by keywords.
    metric_patterns = r'(\d+%|\d+\s*percent|\$\d+|\d+x\b|\d+\s*(?:users|customers|clients|projects|team members|requests|downloads|sales))'
    quantifiable_count = len(re.findall(metric_patterns, text_lower))
    if quantifiable_count >= 2:
        score += 25
        feedback['quantifiable_metrics'] = f"Excellent! Found {quantifiable_count} quantifiable metrics that demonstrate your impact."
    elif quantifiable_count == 1:
        score += 15
        feedback['quantifiable_metrics'] = "Good start! You have one quantifiable metric. Adding more will strengthen your resume."
    else:
        score += 5
        feedback['quantifiable_metrics'] = "Add quantifiable results to show impact (e.g., 'increased efficiency by 20%' or 'managed a team of 5')."

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