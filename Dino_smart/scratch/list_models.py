import json
import google.generativeai as genai

with open('config.json', 'r') as f:
    config = json.load(f)

key = config.get('Gemini_api_key')
genai.configure(api_key=key)

try:
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print("Error listing models:", e)
