import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
API_KEYS = os.getenv("GOOGLE_API_KEYS", "").split(",")

def try_gemini_api(payload):
    for key in API_KEYS:
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": key.strip()
        }
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()
        except:
            continue  # silent fail and try next key
    return {"error": "All API keys failed."}

def generate_llm_suggestions(resume_text, job_title, required_skills, job_description_text):
    if not API_KEYS or not API_KEYS[0]:
        return "❌ API key missing. Check your .env file."
    if len(resume_text.strip()) < 100 or len(job_description_text.strip()) < 100:
        return "❌ Resume or job description is too short."

    prompt = f"""
You are an expert career coach and ATS resume analyst. Given a job description and a user's resume, your task is to identify:

1. Gaps in required skills or experiences.
2. Areas to improve clarity, action verbs, or measurable outcomes.
3. Suggestions to better align the resume with ATS keyword expectations.
4. Tone, format, or style inconsistencies if any.
5. Add any missing project examples, quantified achievements, or modern tools/frameworks.

Return your suggestions as 3 to 6 clear, numbered bullet points. Use **bold** headings for each point. Keep it highly actionable and practical.

---
**Job Title:** {job_title}

**Required Skills for this Role:**
{required_skills}

**Full Job Description:**
{job_description_text}

---

**Resume:**
{resume_text}
"""

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = try_gemini_api(payload)
    if "candidates" in response:
        parts = response["candidates"][0].get("content", {}).get("parts", [])
        return parts[0].get("text", "⚠️ Empty response from Gemini.") if parts else "⚠️ No content returned."
    
    return f"❌ LLM Suggestion Error: {response.get('error', 'Unknown error')}"

def generate_interview_questions(resume_text, experience_level, project_info="", skill_summary=""):
    if not API_KEYS or not API_KEYS[0]:
        return "❌ API key missing. Check your .env file."

    prompt = f"""
You are an expert technical interviewer. Based on the candidate's resume and experience level ({experience_level}), generate the following interview questions:

- 8 Technical Questions based on the candidate's resume and skills.
- 6 Project-Related Questions based on the 'Projects' section.
- 6 HR/Behavioral Questions based on their overall profile.

Format your response as three clearly separated sections, each with a bold section header (e.g., 'Technical Questions', 'Project-Related Questions', 'HR/Behavioral Questions').

For each section:
- Start numbering from 1 for each section (do not continue numbering across sections).
- Use plain text, no markdown, no nested or broken numbering, and no extra symbols.
- Each question should be on its own line, with a number and a period (e.g., '1. ...').
- Do not include any explanations or introductory text, only the questions and section headers.
- Make the questions human-like, scenario-based, and aligned with the candidate's background.

--- RESUME ---
{resume_text}

--- PROJECTS ---
{project_info}

--- SKILLS ---
{skill_summary}
"""

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = try_gemini_api(payload)
    if "candidates" in response:
        parts = response["candidates"][0].get("content", {}).get("parts", [])
        return parts[0].get("text", "⚠️ No questions returned.") if parts else "⚠️ Empty response"

    return f"❌ Interview Question Error: {response.get('error', 'Unknown error')}"
