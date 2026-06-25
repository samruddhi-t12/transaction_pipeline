import os
import httpx
from dotenv import load_dotenv

# Load the key from your .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print(" ERROR: Could not find GEMINI_API_KEY in .env file.")
    exit()

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

# This is the exact prompt structure your Celery worker uses
prompt = """
You are a financial risk analyst. Based on the following transaction data, return a JSON object with EXACTLY these keys:
- 'top_merchants' (a list of the top 3 merchants)
- 'narrative' (a 2-3 sentence spending narrative)
- 'risk_level' (strictly 'low', 'medium', or 'high')

Data:
Total Spend INR: 45000.50
Total Spend USD: 1200.00
Anomaly Count: 5
Top Merchants: Uber, Swiggy, Amazon AWS
"""

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    # Forcing strict JSON output
    "generationConfig": {"response_mime_type": "application/json"} 
}

print("Pinging Gemini to generate the summary...")

try:
    with httpx.Client(timeout=15.0) as client:
        response = client.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            text = data['candidates'][0]['content']['parts'][0]['text']
            print("\n SUCCESS! Here is the JSON summary your API will return:\n")
            print(text)
        else:
            print(f"\n FAILED. Google rejected the request.")
            print(f"Error Details: {response.text}")
except Exception as e:
    print(f"\n CRASH: {e}")