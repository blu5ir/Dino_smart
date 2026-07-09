import sys
import os

print("Initial sys.path:")
for p in sys.path:
    print(" -", p)

try:
    from providers.llm_factory import LLMFactory
    print("Successfully imported LLMFactory:", LLMFactory)
    provider = LLMFactory.get_provider("Gemini", "dummy-key")
    print("Provider created by LLMFactory:", provider)
except Exception as e:
    print("Error importing/using LLMFactory:", e)
