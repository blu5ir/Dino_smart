import os
import base64
import time
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
        
        model_name = model_name or "gemini-3.5-flash"
        if "gemini-1.5-flash" in model_name or "gemini-2.5-flash" in model_name:
            model_name = model_name.replace("gemini-1.5-flash", "gemini-3.5-flash").replace("gemini-2.5-flash", "gemini-3.5-flash")
        elif "gemini-1.5-pro" in model_name or "gemini-2.5-pro" in model_name:
            model_name = model_name.replace("gemini-1.5-pro", "gemini-3.5-flash").replace("gemini-2.5-pro", "gemini-3.5-flash")
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
        def _call(model_name):
            return self._generate_text_with_model(model_name, prompt, system_instruction, temperature, max_tokens)
        try:
            return _execute_with_retry(_call, self.model_name)
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e) or "not supported" in str(e).lower():
                fallback_model = "gemini-3.5-flash"
                if self.model_name != fallback_model:
                    try:
                        return _execute_with_retry(_call, fallback_model)
                    except Exception as fallback_err:
                        raise fallback_err
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
        def _call(model_name):
            return self._generate_image_ocr_with_model(model_name, prompt, image_bytes, mime_type)
        try:
            return _execute_with_retry(_call, self.model_name)
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e) or "not supported" in str(e).lower():
                fallback_model = "gemini-3.5-flash"
                if self.model_name != fallback_model:
                    try:
                        return _execute_with_retry(_call, fallback_model)
                    except Exception as fallback_err:
                        raise fallback_err
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
        
        def _call():
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        return _execute_with_retry(_call)

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
        
        def _call():
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1024
            )
            return response.choices[0].message.content
        return _execute_with_retry(_call)


try:
    import streamlit as st
except ImportError:
    st = None


def _show_toast(message: str, icon: str = None):
    if st is not None:
        try:
            st.toast(message, icon=icon)
        except Exception:
            pass


def _execute_with_retry(func, *args, **kwargs):
    import re
    max_retries = 4
    backoff = 4.0
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            is_rate_limit = (
                "ResourceExhausted" in type(e).__name__ or 
                "429" in str(e) or 
                "quota" in str(e).lower() or
                "rate limit" in str(e).lower()
            )
            if is_rate_limit and attempt < max_retries - 1:
                sleep_time = None
                # Parse exact retry time if specified in the API error message
                match = re.search(r"(?:retry in|retry after|retry\s+delay\s+of)\s+([0-9.]+)\s*s", str(e), re.IGNORECASE)
                if match:
                    try:
                        sleep_time = float(match.group(1)) + 1.5
                    except Exception:
                        pass
                
                if sleep_time is None:
                    sleep_time = backoff * (2 ** attempt)
                
                sleep_time = min(sleep_time, 35.0)
                _show_toast(f"Rate limit hit. Waiting {sleep_time:.1f}s to reset...", icon="⏳")
                time.sleep(sleep_time)
                continue
            raise e


class SmartRouterProvider(BaseLLMProvider):
    def __init__(self, gemini_provider=None, groq_provider=None, openrouter_provider=None):
        self.gemini = gemini_provider
        self.groq = groq_provider
        self.openrouter = openrouter_provider

    def _execute_with_cascade(self, cascade_list, prompt: str, system_instruction: str = None, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        last_error = None
        for provider_name, provider in cascade_list:
            if not provider:
                continue
            
            if provider_name == "Groq":
                _show_toast("Trying Groq (ultra-fast)...", icon="⚡")
            elif provider_name == "OpenRouter":
                _show_toast("Trying OpenRouter...", icon="🌐")
            elif provider_name == "Gemini":
                _show_toast("Trying Gemini...", icon="🧠")
                
            try:
                return provider.generate_text(prompt, system_instruction, temperature, max_tokens)
            except Exception as e:
                last_error = e
                err_str = str(e).split('\n')[0]
                _show_toast(f"{provider_name} failed: {err_str[:40]}. Cascading...", icon="🔄")
                
        if last_error:
            raise last_error
        raise ValueError("No configured providers are available in the Smart Router.")

    def generate_text(self, prompt: str, system_instruction: str = None, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        prompt_len = len(prompt) if prompt else 0
        sys_len = len(system_instruction) if system_instruction else 0
        
        is_large_context = prompt_len > 12000 or sys_len > 3000
        
        is_complex_academic_task = False
        if system_instruction:
            sys_lower = system_instruction.lower()
            if "curriculum designer" in sys_lower or "university professor" in sys_lower or "outline" in sys_lower or "study guide" in sys_lower:
                is_complex_academic_task = True

        if is_large_context or is_complex_academic_task:
            cascade = [
                ("Gemini", self.gemini),
                ("OpenRouter", self.openrouter),
                ("Groq", self.groq)
            ]
        else:
            cascade = [
                ("Groq", self.groq),
                ("OpenRouter", self.openrouter),
                ("Gemini", self.gemini)
            ]

        return self._execute_with_cascade(cascade, prompt, system_instruction, temperature, max_tokens)

    def generate_image_ocr(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        cascade_list = [
            ("Gemini", self.gemini),
            ("OpenRouter", self.openrouter),
            ("Groq", self.groq)
        ]
        
        last_error = None
        for provider_name, provider in cascade_list:
            if not provider:
                continue
            try:
                if provider_name == "Gemini":
                    _show_toast("Routing OCR to Gemini (multimodal)...", icon="👁️")
                else:
                    _show_toast(f"Routing OCR to {provider_name}...", icon="👁️")
                return provider.generate_image_ocr(prompt, image_bytes, mime_type)
            except Exception as e:
                last_error = e
                err_str = str(e).split('\n')[0]
                _show_toast(f"OCR failed on {provider_name}: {err_str[:40]}. Cascading...", icon="🔄")
                
        if last_error:
            raise last_error
        raise ValueError("No providers available for image OCR in Smart Router.")


class LLMFactory:
    @staticmethod
    def get_provider(provider_name=None, api_key=None, model_name=None, base_url=None):
        if not provider_name:
            return None
            
        provider_name_lower = provider_name.lower()
        
        if "smart router" in provider_name_lower:
            import json
            config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(config_dir, "config.json")
            
            gemini_key = ""
            gemini_model = "gemini-3.5-flash"
            groq_key = ""
            groq_model = "llama-3.1-8b-instant"
            groq_base_url = "https://api.groq.com/openai/v1"
            openrouter_key = ""
            openrouter_model = "meta-llama/llama-3.1-8b-instruct:free"
            openrouter_base_url = "https://openrouter.ai/api/v1"
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        cfg = json.load(f)
                        gemini_key = cfg.get("Gemini_api_key", "")
                        gemini_model = cfg.get("Gemini_model_name", "gemini-3.5-flash")
                        groq_key = cfg.get("Groq_api_key", "")
                        groq_model = cfg.get("Groq_model_name", "llama-3.1-8b-instant")
                        groq_base_url = cfg.get("Groq_base_url", "https://api.groq.com/openai/v1")
                        openrouter_key = cfg.get("OpenRouter_api_key", "")
                        openrouter_model = cfg.get("OpenRouter_model_name", "meta-llama/llama-3.1-8b-instruct:free")
                        openrouter_base_url = cfg.get("OpenRouter_base_url", "https://openrouter.ai/api/v1")
                except Exception:
                    pass
            
            if not gemini_key:
                gemini_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
            if not groq_key:
                groq_key = os.environ.get("GROQ_API_KEY", "")
            if not openrouter_key:
                openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
                
            gemini_prov = None
            if gemini_key:
                try:
                    gemini_prov = GeminiProvider(api_key=gemini_key, model_name=gemini_model)
                except Exception:
                    pass
                    
            groq_prov = None
            if groq_key:
                try:
                    groq_prov = OpenAICompatibleProvider(api_key=groq_key, model_name=groq_model, base_url=groq_base_url)
                except Exception:
                    pass
                    
            openrouter_prov = None
            if openrouter_key:
                try:
                    openrouter_prov = OpenAICompatibleProvider(api_key=openrouter_key, model_name=openrouter_model, base_url=openrouter_base_url)
                except Exception:
                    pass
                    
            return SmartRouterProvider(
                gemini_provider=gemini_prov,
                groq_provider=groq_prov,
                openrouter_provider=openrouter_prov
            )
            
        elif "gemini" in provider_name_lower:
            return GeminiProvider(api_key=api_key, model_name=model_name)
            
        elif "groq" in provider_name_lower:
            return OpenAICompatibleProvider(
                api_key=api_key, 
                model_name=model_name or "llama-3.1-8b-instant", 
                base_url=base_url or "https://api.groq.com/openai/v1"
            )
            
        elif "openrouter" in provider_name_lower or "open router" in provider_name_lower:
            return OpenAICompatibleProvider(
                api_key=api_key, 
                model_name=model_name or "meta-llama/llama-3.1-8b-instruct:free", 
                base_url=base_url or "https://openrouter.ai/api/v1"
            )
            
        else:
            return OpenAICompatibleProvider(api_key=api_key, model_name=model_name, base_url=base_url)
