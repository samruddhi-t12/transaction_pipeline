import json
import time
import httpx
from app.core.config import settings

def call_gemini_with_retry(prompt: str, max_retries: int = 3):
    """Calls Gemini 1.5 Flash with exponential backoff and forces JSON output."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    for attempt in range(max_retries):
        try:
            # FAILURE PATH: We must use a timeout. If Google's servers hang, our worker shouldn't freeze forever.
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                raw_text = data['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_text)
                
        except Exception as e:
            print(f"LLM Call Failed (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None # If we fail 3 times, return None so the pipeline doesn't crash
            
            # EXPONENTIAL BACKOFF: Sleep for 2 seconds, then 4 seconds...
            time.sleep(2 ** (attempt + 1))