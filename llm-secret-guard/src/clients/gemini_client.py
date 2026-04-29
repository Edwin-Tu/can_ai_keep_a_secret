import os
from typing import List, Dict
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiClient:
    """Gemini API client using google-genai SDK."""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        if not GEMINI_AVAILABLE:
            raise RuntimeError(
                "google-genai SDK not installed. "
                "Install it with: pip install google-genai"
            )
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable not set.\n"
                "Please set it with: export GEMINI_API_KEY='your_api_key_here'"
            )
        
        self.client = genai.Client(api_key=api_key)
        self.model = model_name

    def __init__(self, model: str = "gemini-2.0-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("未找到 GEMINI_API_KEY，请在 .env 中设置。")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0, max_tokens: int = 300) -> str:
        """
        Generate response using Gemini API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature (default 0).
            max_tokens: Max tokens to generate.
        
        Returns:
            Response text.
        """
        # Extract system prompt and user messages
        system_prompt = ""
        user_contents = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                user_contents.append(msg["content"])
        
        # Combine all user messages
        contents = "\n".join(user_contents) if user_contents else ""
        
        # Build config
        config = types.GenerateContentConfig(
            system_instruction=system_prompt if system_prompt else None,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                config=config,
                contents=contents,
            )
            return response.text or ""
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")


def get_gemini_client(model_name: str = "gemini-2.5-flash") -> GeminiClient:
    """Factory function to create GeminiClient."""
    return GeminiClient(model_name=model_name)
