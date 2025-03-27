# neuroerp/ai_agents/services/ollama_service.py
import requests
import logging
from django.conf import settings

logger = logging.getLogger('neuroerp.ai_agents')

class OllamaService:
    """
    Service for interacting with Ollama AI models
    """
    def __init__(self, model=None):
        """
        Initialize Ollama service with a specific model or default
        """
        self.base_url = settings.OLLAMA_API_BASE
        self.model = model or settings.DEFAULT_MODEL
        self.headers = {
            'Content-Type': 'application/json'
        }

    def generate(self, prompt, max_tokens=None, temperature=None):
        """
        Generate text response from Ollama
        """
        try:
            payload = {
                'model': self.model,
                'prompt': prompt,
                'stream': False
            }

            # Optional parameters
            if max_tokens:
                payload['max_tokens'] = max_tokens
            if temperature:
                payload['temperature'] = temperature

            response = requests.post(
                f'{self.base_url}/api/generate', 
                json=payload, 
                headers=self.headers
            )
            response.raise_for_status()
            
            return response.json().get('response', '')
        
        except requests.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            return f"Error generating response: {e}"

    def list_models(self):
        """
        List available Ollama models
        """
        try:
            response = requests.get(f'{self.base_url}/api/tags')
            response.raise_for_status()
            return response.json().get('models', [])
        except requests.RequestException as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

# Example AI Agent for Finance
class FinanceAgent:
    """
    AI Agent specialized in financial analysis and insights
    """
    def __init__(self):
        self.ollama_service = OllamaService()

    def analyze_financial_data(self, financial_data):
        """
        Analyze financial data and provide insights
        """
        prompt = f"""
        Analyze the following financial data and provide key insights:
        {financial_data}

        Provide:
        1. Key financial performance indicators
        2. Potential risks
        3. Optimization recommendations
        """
        
        return self.ollama_service.generate(prompt)

# Example AI Agent for HR
class HRAgent:
    """
    AI Agent specialized in human resources management
    """
    def __init__(self):
        self.ollama_service = OllamaService()

    def generate_job_description(self, role_details):
        """
        Generate a comprehensive job description