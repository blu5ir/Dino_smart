from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """Abstract base class representing an LLM Provider."""
    
    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: str = None, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        """Generate text from a prompt."""
        pass

    @abstractmethod
    def generate_image_ocr(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        """Perform OCR/text extraction from an image using vision LLM capabilities."""
        pass
