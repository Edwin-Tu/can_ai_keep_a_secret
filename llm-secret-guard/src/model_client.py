"""
模型 client 選擇器。

目前專案先聚焦：
- mock：測試流程用假模型
- ollama:<model_name>：本地開源模型

已移除：
- openai
- gemini
- anthropic / claude

原因：
第一階段目標是本地端大量測試開源模型，避免 API key、費用與雲端依賴。
"""

from clients.mock_client import MockClient
from clients.ollama_client import OllamaClient


def get_client(model_name: str):
    if not model_name:
        raise ValueError("model_name 不可為空")

    model_name_lower = model_name.lower()

    if model_name_lower == "mock":
        return MockClient()

    if model_name_lower.startswith("ollama:"):
        ollama_model = model_name.split("ollama:", 1)[1]
        if not ollama_model:
            raise ValueError("Ollama model name is empty. Example: ollama:qwen2.5:3b")
        return OllamaClient(model_name=ollama_model)

    raise ValueError(
        f"Unsupported model: {model_name}. "
        "目前僅支援 mock 與 ollama:<model_name>。"
    )
