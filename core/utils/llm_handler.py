import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True) 

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
API_KEY = os.getenv("GOOGLE_API_KEY")

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY
}
def generate_llm_suggestions(resume_text, job_title, required_skills, job_description_text):
    if not API_KEY:
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
                "role": "user",  # REQUIRED for 1.5 Flash
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code != 200:
            return f"❌ Could not generate suggestions (HTTP {response.status_code})"

        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return parts[0].get("text", "⚠️ Empty response from Gemini.") if parts else "⚠️ No content returned."

    except requests.exceptions.RequestException:
        return "❌ Network error when calling Gemini API."
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"


def generate_interview_questions(resume_text, experience_level, project_info="", skill_summary=""):
    prompt = f"""
You are an expert technical interviewer. Based on the candidate's resume and experience level ({experience_level}), generate the following interview questions:

- 8 technical questions based on the candidate's resume and skills.
- 6 project-related questions based on the 'Projects' section.
- 6 HR/behavioral questions based on their overall profile.

Make sure:
- Only return the questions in plain text format.dont use unnecessary symbols and even the text written inside().they should be just like the questions asked by an interviewer.
- No generic questions like "What is Python?",such questions are allowed but very rare,eventhough such questions are there they should not be as generic question.
- Use follow-up or real-world situation framing where possible but not in all questions.
- Number each question clearly.
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

    try:
        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            return f"❌ Error {response.status_code} generating interview questions"

        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return parts[0].get("text", "⚠️ No questions returned.") if parts else "⚠️ Empty response"

    except Exception as e:
        return f"❌ Interview Question Error: {str(e)}"
