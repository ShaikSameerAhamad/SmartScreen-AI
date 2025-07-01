# core/utils/llm_handler.py
import os
import requests
import json

# --- NEW: Configuration for Google Gemini API ---
# We use "gemini-pro" as it's a stable and powerful model for this task.
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={os.getenv('GOOGLE_API_KEY')}"
headers = {"Content-Type": "application/json"}

def generate_llm_suggestions(resume_text, job_description_text):
    # The prompt remains the same, as it's high-quality
    prompt = f"""
    As an expert career coach, your task is to provide constructive feedback on a resume based on a specific job description.

    **Job Description:**
    ---
    {job_description_text}
    ---

    **User's Resume Text:**
    ---
    {resume_text}
    ---

    **Your Task:**
    Provide a concise, actionable critique in 2-3 paragraphs. Focus on:
    1.  Overall alignment with the role.
    2.  Specific strengths to emphasize.
    3.  Key areas for improvement or skills to highlight more effectively.
    
    Do not just list missing skills. Provide strategic advice.
    """

    # --- NEW: Payload structure for Gemini API ---
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            error_message = f"API request failed with status code {response.status_code}. Response: {response.text}"
            print(f"LLM API Error: {error_message}")
            return f"Could not generate AI suggestions due to an API error. (Status: {response.status_code})"

        output = response.json()

        # --- NEW: Parsing logic for Gemini's response structure ---
        if 'candidates' in output and output['candidates']:
            # Check if 'parts' exists and is not empty
            if 'parts' in output['candidates'][0]['content'] and output['candidates'][0]['content']['parts']:
                return output['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Handle cases where the response might be blocked or have an error
        print(f"LLM API Error: Unexpected response format or content blocked: {output}")
        return "Could not generate AI suggestions. The response may have been blocked for safety reasons or was in an unexpected format."


    except requests.exceptions.RequestException as e:
        print(f"An exception occurred while querying the LLM: {e}")
        return "An error occurred while connecting to the AI suggestion service."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "An unexpected error occurred while generating suggestions."
