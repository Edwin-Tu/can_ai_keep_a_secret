from typing import List, Dict


class AnthropicClient:
    """
    TODO: 串接 Anthropic Claude API。
    建議之後使用官方 SDK 實作。
    """

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0, max_tokens: int = 300) -> str:
        raise NotImplementedError("Anthropic API client 尚未實作。")
