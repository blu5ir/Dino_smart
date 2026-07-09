import json
from openai import OpenAI

with open('config.json', 'r') as f:
    config = json.load(f)

# Test Groq
groq_key = config.get('Groq_api_key')
groq_base = config.get('Groq_base_url', 'https://api.groq.com/openai/v1')
groq_model = config.get('Groq_model_name', 'llama-3.1-8b-instant')

print(f"Testing Groq: {groq_model}")
try:
    client = OpenAI(api_key=groq_key, base_url=groq_base)
    response = client.chat.completions.create(
        model=groq_model,
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    print("Groq Success:", response.choices[0].message.content)
except Exception as e:
    print("Groq Error:", e)

# Test DeepSeek
ds_key = config.get('DeepSeek_api_key')
ds_base = config.get('DeepSeek_base_url', 'https://api.deepseek.com')
ds_model = config.get('DeepSeek_model_name', 'deepseek-chat')

print(f"\nTesting DeepSeek: {ds_model}")
try:
    client = OpenAI(api_key=ds_key, base_url=ds_base)
    response = client.chat.completions.create(
        model=ds_model,
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    print("DeepSeek Success:", response.choices[0].message.content)
except Exception as e:
    print("DeepSeek Error:", e)
