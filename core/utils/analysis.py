# core/utils/analysis.py

import re
import os
import spacy
import pdfplumber
import docx
import pytesseract
from PIL import Image
from spacy.matcher import PhraseMatcher
from pdf2image import convert_from_bytes
import io # Required for in-memory processing

# --- (WINDOWS ONLY) TESSERACT CONFIGURATION ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\91944\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


# --- 1. SETUP NLP MODEL AND SKILL LIST ---
nlp = spacy.load("en_core_web_lg")
SKILL_KEYWORDS = [
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'html', 'css', 'sass', 'less',
    'react', 'angular', 'vue', 'svelte', 'nodejs', 'express.js', 'next.js', 'gatsby',
    'django', 'flask', 'fastapi', 'spring boot', 'ruby on rails',
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'sqlite', 'nosql',
    'aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'helm',
    'git', 'github', 'gitlab', 'ci/cd', 'jenkins', 'circleci', 'travis ci',
    'data analysis', 'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'power bi', 'tableau',
    'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
    'nlp', 'natural language processing', 'spacy', 'nltk', 'hugging face', 'transformers',
    'devops', 'agile', 'scrum', 'jira', 'confluence', 'project management',
    'rest api', 'graphql', 'soap', 'microservices',
    'linux', 'unix', 'bash', 'powershell', 'scripting',
    'cybersecurity', 'penetration testing', 'encryption', 'firewalls',
    'networking', 'tcp/ip', 'dns', 'http',
    'data structures', 'algorithms', 'object-oriented programming', 'oop', 'functional programming',
    'sap', 'xml'
]


# --- 2. IMPROVED RESUME PARSING & CLEANING (NOW WITH IN-MEMORY SUPPORT) ---
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'[^\w\s@.-]', '', text)
    return text.strip().lower()

from pdf2image import convert_from_bytes
import io

def extract_text(uploaded_file):
    import re
    from PIL import Image
    import pytesseract
    import docx

    # Always read file once and reuse
    uploaded_file.seek(0)
    file_content = uploaded_file.read()
    file_buffer = io.BytesIO(file_content)
    text = ""

    filename = uploaded_file.name
    _, extension = os.path.splitext(filename)
    extension = extension.lower()

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
            for para in doc.paragraphs:
                text += para.text + "\n"

        elif extension == '.txt':
            text = file_content.decode('utf-8', errors='ignore')

        elif extension in ['.jpg', '.jpeg', '.png']:
            image = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(image)

    except Exception as e:
        print(f"[ERROR] extract_text failed for {filename}: {e}")
        return ""

    def clean_text(t):
        t = re.sub(r'\s+', ' ', t)
        t = re.sub(r'[\r\n]+', ' ', t)
        t = re.sub(r'[^\w\s@.-]', '', t)
        return t.strip().lower()

    return clean_text(text)



# --- 3. ADVANCED SKILL EXTRACTION ---
def extract_skills(text):
    matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
    patterns = [nlp.make_doc(skill) for skill in SKILL_KEYWORDS]
    matcher.add("SKILL_MATCHER", patterns)
    doc = nlp(text)
    matches = matcher(doc)
    found_skills = set()
    for _, start, end in matches:
        span = doc[start:end]
        found_skills.add(span.text)
    return list(found_skills)


# --- 4. AI RESUME GRADING (RULE-BASED) ---
def grade_resume(text):
    feedback = {}
    score = 0
    word_count = len(text.split())
    if word_count < 200:
        score += 5
        feedback['length'] = f"Resume is very brief ({word_count} words). Consider expanding on your experience. Aim for 400-800 words."
    elif 400 <= word_count <= 800:
        score += 25
        feedback['length'] = f"Good length ({word_count} words). Concise and effective."
    else:
        score += 15
        feedback['length'] = f"Consider adjusting length ({word_count} words). Ideal is 400-800 words."
    sections_found = [s for s in ['experience', 'skills', 'education', 'projects'] if re.search(r'\b' + s + r'\b', text, re.IGNORECASE)]
    if len(sections_found) >= 2:
        score += 25
    feedback['sections'] = f"Found {len(sections_found)} key sections. Consider adding any that are missing."
    action_verbs = ['developed', 'led', 'managed', 'created', 'implemented', 'designed', 'optimized', 'analyzed', 'built']
    verb_count = sum(1 for verb in action_verbs if verb in text)
    if verb_count >= 3:
        score += 25
        feedback['action_verbs'] = f"Good use of action verbs ({verb_count} found)."
    else:
        score += 10
        feedback['action_verbs'] = "Use more powerful action verbs (e.g., 'developed', 'managed', 'optimized')."
    quantifiable_count = len(re.findall(r'(\d+%|\d+\s*percent|\$\d+|\d+x\b)', text))
    if quantifiable_count >= 1:
        score += 25
        feedback['quantifiable_results'] = f"Excellent! Found {quantifiable_count} quantifiable result(s)."
    else:
        score += 10
        feedback['quantifiable_results'] = "Add quantifiable results to show impact (e.g., 'increased efficiency by 20%')."
    return min(score, 100), feedback


# --- 5. MAIN ANALYSIS FUNCTION ---
def perform_full_analysis(resume_text, job_role_model):
    if not resume_text or not resume_text.strip():
        return {
            "match_score": 0,
            "missing_skills": job_role_model.get_skills_list(),
            "ai_suggestions": "Could not extract any text from the uploaded file. Please ensure it is not a corrupted file and that Tesseract is correctly configured for image files.",
            "resume_grade": 0,
            "grading_feedback": {"error": "Text extraction failed."}
        }
    required_skills = job_role_model.get_skills_list()
    resume_skills = extract_skills(resume_text)
    matched_skills = set(resume_skills) & set(required_skills)
    missing_skills = set(required_skills) - set(resume_skills)
    score = (len(matched_skills) / len(required_skills)) * 100 if required_skills else 0
    if not missing_skills:
        suggestions = "Excellent! Your resume appears to have all the key skills required for this role."
    else:
        suggestions = f"To better align with this role, focus on these missing skills: {', '.join(missing_skills)}. If you have experience with them, make sure they are explicitly mentioned."
    grade, grading_feedback = grade_resume(resume_text)
    return {
        "match_score": round(score, 2),
        "missing_skills": list(missing_skills),
        "ai_suggestions": suggestions,
        "resume_grade": grade,
        "grading_feedback": grading_feedback
    }
