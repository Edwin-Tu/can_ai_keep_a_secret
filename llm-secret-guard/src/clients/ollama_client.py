"""
Ollama local model client.

Uses the local Ollama chat API:
http://localhost:11434/api/chat
"""

from __future__ import annotations

from typing import Dict, List, Optional
import requests


def _ns_to_seconds(value) -> str:
    try:
        if value in (None, ""):
            return ""
        return str(round(float(value) / 1_000_000_000, 3))
    except (TypeError, ValueError):
        return ""


def _tokens_per_second(eval_count, eval_duration) -> str:
    try:
        count = float(eval_count)
        seconds = float(eval_duration) / 1_000_000_000
        if count <= 0 or seconds <= 0:
            return ""
        return str(round(count / seconds, 2))
    except (TypeError, ValueError, ZeroDivisionError):
        return ""


class OllamaClient:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.last_metadata: Dict[str, object] = {}

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0,
        max_tokens: Optional[int] = None,
    ) -> str:
        options = {"temperature": temperature}

        # max_tokens=None means no explicit num_predict limit is sent to Ollama.
        if max_tokens is not None and max_tokens > 0:
            options["num_predict"] = max_tokens

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": options,
            "keep_alive": "10m",
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=None,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                "Cannot connect to Ollama. Please make sure Ollama is installed, "
                "running, and available at http://localhost:11434."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                "Ollama request timed out. This should only happen if a timeout "
                "is configured by the caller or environment."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(f"Ollama API returned an HTTP error: {exc}") from exc

        total_duration = data.get("total_duration")
        load_duration = data.get("load_duration")
        prompt_eval_duration = data.get("prompt_eval_duration")
        eval_count = data.get("eval_count")
        eval_duration = data.get("eval_duration")

        self.last_metadata = {
            "total_duration": total_duration,
            "total_duration_sec": _ns_to_seconds(total_duration),
            "load_duration": load_duration,
            "load_duration_sec": _ns_to_seconds(load_duration),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "prompt_eval_duration": prompt_eval_duration,
            "prompt_eval_duration_sec": _ns_to_seconds(prompt_eval_duration),
            "eval_count": eval_count,
            "eval_duration": eval_duration,
            "eval_duration_sec": _ns_to_seconds(eval_duration),
            "tokens_per_second": _tokens_per_second(eval_count, eval_duration),
        }

        return data.get("message", {}).get("content", "")
