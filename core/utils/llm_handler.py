# core/utils/llm_handler.py
import os
import requests
import json

# --- Configuration for Google Gemini API ---
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={os.getenv('GOOGLE_API_KEY')}"
headers = {"Content-Type": "application/json"}

def generate_llm_suggestions(resume_text, job_description_text):
    # --- THIS IS THE UPDATED PROMPT ---
    prompt = f"""
    As an expert career coach, your task is to provide a concise, actionable critique of a resume based on a specific job description.

    **Job Description:**
    ---
    {job_description_text}
    ---

    **User's Resume Text:**
    ---
    {resume_text}
    ---

    **Your Task:**
    Format your entire response as a list of 3-5 important bullet points. Each bullet point must be a specific, actionable recommendation for how the user can improve their resume to better match this job. Start each point with a clear heading in bold.
    """

    # Payload structure for Gemini API
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        # Add safety settings to reduce the chance of the response being blocked
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
            error_message = f"API request failed with status code {response.status_code}. Response: {response.text}"
            print(f"LLM API Error: {error_message}")
            return f"Could not generate AI suggestions due to an API error. (Status: {response.status_code})"

        output = response.json()
        
        # Check for candidates and parts before accessing them
        if 'candidates' in output and output['candidates']:
            content = output['candidates'][0].get('content', {})
            if 'parts' in content and content['parts']:
                return content['parts'][0].get('text', 'The model returned an empty suggestion.').strip()
        
        # Handle cases where the response might be blocked for safety reasons
        if 'promptFeedback' in output and output['promptFeedback'].get('blockReason'):
            reason = output['promptFeedback']['blockReason']
            print(f"LLM content blocked. Reason: {reason}")
            return "Could not generate AI suggestions because the prompt was blocked for safety reasons. Please try rephrasing the job description."
        
        print(f"LLM API Error: Unexpected response format: {output}")
        return "Could not parse the model's response."


    except requests.exceptions.RequestException as e:
        print(f"An exception occurred while querying the LLM: {e}")
        return "An error occurred while connecting to the AI suggestion service."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "An unexpected error occurred while generating suggestions."