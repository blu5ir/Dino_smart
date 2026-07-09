import json
import os
import google.generativeai as genai

with open('config.json', 'r') as f:
    config = json.load(f)

key = config.get('Gemini_api_key')
print(f"Key format checks: starts with AQ: {key.startswith('AQ')}, length: {len(key)}")

genai.configure(api_key=key)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
    print("Success:", response.text)
except Exception as e:
    print("Error:", e)
