import os
import shutil

# Remove all old files to avoid any residual issues
shutil.rmtree("components", ignore_errors=True)
os.makedirs("components", exist_ok=True)

# Define correct content for each file (using double triple quotes to allow single triple quotes inside)
files = {
    "custom_styles.py": r"""import streamlit as st

def apply_custom_styles():
    st.markdown('''
        <style>
        .gradient-title {
            background: linear-gradient(90deg, #34d399, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        .metric-card {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .metric-label {
            font-size: 0.9rem;
            color: #94a3b8;
        }
        .metric-val {
            font-size: 1.8rem;
            font-weight: bold;
            color: #e2e8f0;
        }
        .glass-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        </style>
    ''', unsafe_allow_html=True)
""",

    "flashcard_card.py": r"""import streamlit as st

def render_flashcard(front, back):
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'**📖 Front:** {front}')
        with col2:
            st.markdown(f'**📝 Back:** {back}')
""",

    "mermaid_renderer.py": r"""import streamlit as st

def render_mermaid(code):
    st.code(code, language='mermaid')
    st.caption('📊 Mermaid diagram rendered in code block above.')
"""
}

for filename, content in files.items():
    with open(os.path.join("components", filename), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Created components/{filename}")

# Ensure providers directory exists with LLMFactory
os.makedirs("providers", exist_ok=True)
if not os.path.exists("providers/llm_factory.py"):
    with open("providers/llm_factory.py", "w", encoding="utf-8") as f:
        f.write('''import os
import base64
from .base_provider import BaseLLMProvider

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key, model_name=None):
        if not HAS_GEMINI:
            raise ImportError("google-generativeai package is not installed. Run 'pip install google-generativeai'.")
        if not api_key:
            raise ValueError("API Key is required for Gemini Provider.")
        genai.configure(api_key=api_key)
        
        # Auto-upgrade deprecated gemini-1.5 models to gemini-2.5
        model_name = model_name or "gemini-2.5-flash"
        if "gemini-1.5-flash" in model_name:
            model_name = model_name.replace("gemini-1.5-flash", "gemini-2.5-flash")
        elif "gemini-1.5-pro" in model_name:
            model_name = model_name.replace("gemini-1.5-pro", "gemini-2.5-pro")
            
        self.model_name = model_name

    def _generate_text_with_model(self, model_name: str, prompt: str, system_instruction: str = None, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            generation_config=generation_config
        )
        response = model.generate_content(prompt)
        return response.text

    def generate_text(self, prompt: str, system_instruction: str = None, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        try:
            return self._generate_text_with_model(self.model_name, prompt, system_instruction, temperature, max_tokens)
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e) or "not supported" in str(e).lower():
                fallback_model = "gemini-2.5-flash"
                if self.model_name != fallback_model:
                    return self._generate_text_with_model(fallback_model, prompt, system_instruction, temperature, max_tokens)
            raise e

    def _generate_image_ocr_with_model(self, model_name: str, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content([
            {
                "mime_type": mime_type,
                "data": image_bytes
            },
            prompt
        ])
        return response.text

    def generate_image_ocr(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        try:
            return self._generate_image_ocr_with_model(self.model_name, prompt, image_bytes, mime_type)
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e) or "not supported" in str(e).lower():
                fallback_model = "gemini-2.5-flash"
                if self.model_name != fallback_model:
                    return self._generate_image_ocr_with_model(fallback_model, prompt, image_bytes, mime_type)
            raise e


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, api_key, model_name, base_url=None):
        if not HAS_OPENAI:
            raise ImportError("openai package is not installed. Run 'pip install openai'.")
        self.client = OpenAI(api_key=api_key or "dummy-key", base_url=base_url)
        self.model_name = model_name

    def generate_text(self, prompt: str, system_instruction: str = None, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    def generate_image_ocr(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=1024
        )
        return response.choices[0].message.content


class LLMFactory:
    @staticmethod
    def get_provider(provider_name=None, api_key=None, model_name=None, base_url=None):
        if not provider_name:
            return None
            
        provider_name_lower = provider_name.lower()
        
        if "gemini" in provider_name_lower:
            return GeminiProvider(api_key=api_key, model_name=model_name)
            
        elif "openai" in provider_name_lower:
            return OpenAICompatibleProvider(api_key=api_key, model_name=model_name or "gpt-4o-mini", base_url=base_url)
            
        elif "deepseek" in provider_name_lower:
            return OpenAICompatibleProvider(
                api_key=api_key, 
                model_name=model_name or "deepseek-chat", 
                base_url=base_url or "https://api.deepseek.com/v1"
            )
            
        elif "groq" in provider_name_lower:
            return OpenAICompatibleProvider(
                api_key=api_key, 
                model_name=model_name or "llama-3.3-70b-versatile", 
                base_url=base_url or "https://api.groq.com/openai/v1"
            )
            
        elif "ollama" in provider_name_lower:
            return OpenAICompatibleProvider(
                api_key=api_key or "ollama", 
                model_name=model_name or "llama3", 
                base_url=base_url or "http://localhost:11434/v1"
            )
            
        elif "lm studio" in provider_name_lower:
            return OpenAICompatibleProvider(
                api_key=api_key or "lm-studio", 
                model_name=model_name, 
                base_url=base_url or "http://localhost:1234/v1"
            )
            
        elif "openrouter" in provider_name_lower:
            return OpenAICompatibleProvider(
                api_key=api_key, 
                model_name=model_name or "openai/gpt-4o-mini", 
                base_url=base_url or "https://openrouter.ai/api/v1"
            )
            
        elif "huggingface" in provider_name_lower:
            return OpenAICompatibleProvider(
                api_key=api_key, 
                model_name=model_name, 
                base_url=base_url or "https://api-inference.huggingface.co/v1"
            )
            
        else:
            return OpenAICompatibleProvider(api_key=api_key, model_name=model_name, base_url=base_url)
''')
    print("[OK] Created providers/llm_factory.py")
else:
    print("[OK] Skipped providers/llm_factory.py (already exists)")

with open("providers/__init__.py", "w", encoding="utf-8") as f:
    f.write("# Provider module\n")

print("[OK] Finished providers setup")

# Clear cache to remove any compiled bytecode
import shutil
shutil.rmtree("__pycache__", ignore_errors=True)
shutil.rmtree("components/__pycache__", ignore_errors=True)
print("[OK] Cleared __pycache__ folders")

print("\nAll files fixed! Now run: streamlit run app.py")
