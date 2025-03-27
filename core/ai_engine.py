import os
import requests
from typing import Dict, Any, List

class OllamaInterface:
    """Interface to communicate with Ollama models"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or os.environ.get("OLLAMA_HOST", "localhost")
        self.port = port or int(os.environ.get("OLLAMA_PORT", "11434"))
        self.base_url = f"http://{self.host}:{self.port}"
        
    def generate(self, model: str, prompt: str, params: Dict[str, Any] = None) -> str:
        """Generate a response from the specified Ollama model"""
        url = f"{self.base_url}/api/generate"
        
        default_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 1024,
        }
        
        if params:
            default_params.update(params)
            
        payload = {
            "model": model,
            "prompt": prompt,
            **default_params
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json().get("response", "")
    
    def list_models(self) -> List[str]:
        """List available models"""
        url = f"{self.base_url}/api/tags"
        response = requests.get(url)
        response.raise_for_status()
        
        return [model["name"] for model in response.json().get("models", [])]

class AIEngine:
    """Core AI orchestration layer"""
    
    def __init__(self):
        self.ollama = OllamaInterface()
        self.active_agents = {}
        
    def get_agent_response(self, agent_type: str, prompt: str, context: Dict[str, Any] = None) -> str:
        """Get a response from a specific agent type"""
        model_mapping = {
            "finance": "finance",
            "hr": "hr",
            "supply_chain": "supply_chain",
            "general": "general"
        }
        
        model = model_mapping.get(agent_type, "general")
        
        # Prepare context for the prompt if provided
        if context:
            context_str = "\nContext:\n" + "\n".join([f"{k}: {v}" for k, v in context.items()])
            prompt = prompt + context_str
        
        return self.ollama.generate(model, prompt)