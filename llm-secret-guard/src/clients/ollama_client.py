"""
Ollama 本地模型客戶端框架

用於與本地 Ollama 伺服器通信。
TODO: 具體實現待補充
"""

import requests
from typing import List, Dict


class OllamaClient:
    """
    Ollama 本地模型客戶端
    
    用於執行本地開源模型測試。
    """
    
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        """
        初始化 Ollama 客戶端
        
        Args:
            model_name: 模型名稱，例如 "qwen2.5:3b", "llama3.1:8b"
            base_url: Ollama 伺服器 URL，預設 http://localhost:11434
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0, max_tokens: int = 300) -> str:
        """
        呼叫 Ollama 模型生成回應
        
        Args:
            messages: 訊息列表，格式 [{"role": "user/assistant/system", "content": "..."}]
            temperature: 溫度參數，控制隨機性
            max_tokens: 最大生成 token 數量
            
        Returns:
            模型生成的文字回應
            
        Raises:
            NotImplementedError: 方法尚未實現
        """
        raise NotImplementedError("Ollama 客戶端實現待補充")
