"""
Model client selector.

The python_automation branch focuses on:
- mock: deterministic test client
- ollama:<model>: local Ollama models

Cloud API clients are intentionally not wired into the first automation pass.
"""

from clients.mock_client import MockClient
from clients.ollama_client import OllamaClient


def get_client(model_name: str):
    if not model_name:
        raise ValueError("model_name cannot be empty")

    model_name_lower = model_name.lower()

    if model_name_lower == "mock":
        return MockClient()

    if model_name_lower.startswith("ollama:"):
        ollama_model = model_name.split("ollama:", 1)[1]
        if not ollama_model:
            raise ValueError("Ollama model name is empty. Example: ollama:llama3.2:1b")
        return OllamaClient(model_name=ollama_model)

    raise ValueError(
        f"Unsupported model: {model_name}. "
        "Supported models in this branch: mock, ollama:<model_name>."
    )
