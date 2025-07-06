# core/utils/llm_handler.py
import os
import requests
import json

# --- Configuration for Google Gemini API ---
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={os.getenv('GOOGLE_API_KEY')}"
headers = {"Content-Type": "application/json"}

def generate_llm_suggestions(resume_text, job_description_text):
    if len(resume_text.strip()) < 100 or len(job_description_text.strip()) < 100:
        return "Insufficient content for AI suggestions. Please upload a more detailed resume or job description."

    # Build prompt with system-style instruction
    prompt = f"""
You are an expert career coach and ATS resume analyst. Given a job description and a user's resume, your task is to identify:

1. Gaps in required skills or experiences.
2. Areas to improve clarity, action verbs, or measurable outcomes.
3. Suggestions to better align the resume with ATS keyword expectations.
4. Tone, format, or style inconsistencies if any.
5. Add any missing project examples, quantified achievements, or modern tools/frameworks.

Return your suggestions as 3 to 6 clear, numbered bullet points. Use **bold** headings for each point. Keep it highly actionable and practical.

---

**Job Description:**
{job_description_text}

---

**Resume:**
{resume_text}
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code != 200:
            return f"Could not generate suggestions (HTTP {response.status_code})"

        output = response.json()
        if 'candidates' in output and output['candidates']:
            content = output['candidates'][0].get('content', {})
            if 'parts' in content and content['parts']:
                return content['parts'][0].get('text', 'The model returned no suggestions.').strip()

        if 'promptFeedback' in output and output['promptFeedback'].get('blockReason'):
            return "Prompt blocked by safety filters. Try using a different job/resume input."

        return "The model returned an empty response."

    except requests.exceptions.RequestException as e:
        return "Network error while calling AI suggestion service."
    except Exception as e:
        return "Unexpected error during suggestion generation."
