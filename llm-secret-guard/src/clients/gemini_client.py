from typing import List, Dict


class GeminiClient:
    """
    TODO: 串接 Google Gemini API。
    建議之後使用官方 SDK 實作。
    """

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0, max_tokens: int = 300) -> str:
        raise NotImplementedError("Gemini API client 尚未實作。")
