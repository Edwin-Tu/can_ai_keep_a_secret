"""
Ollama 本地模型客戶端。

此 client 用於呼叫本機 Ollama API：
http://localhost:11434/api/chat
"""

from __future__ import annotations

from typing import Dict, List
import requests


class OllamaClient:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.last_metadata: Dict[str, object] = {}

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0,
        max_tokens: int = 300,
    ) -> str:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "keep_alive": "10m",
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=180,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                "無法連線到 Ollama。請確認已安裝並啟動 Ollama，"
                "且 http://localhost:11434 可連線。"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError("Ollama 回應逾時，請改用較小模型或提高 timeout。") from exc
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(f"Ollama API 回傳錯誤：{exc}") from exc

        self.last_metadata = {
            "total_duration": data.get("total_duration"),
            "load_duration": data.get("load_duration"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "prompt_eval_duration": data.get("prompt_eval_duration"),
            "eval_count": data.get("eval_count"),
            "eval_duration": data.get("eval_duration"),
        }

        return data.get("message", {}).get("content", "")
