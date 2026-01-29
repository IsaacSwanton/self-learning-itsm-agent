"""
Ollama LLM Client

Provides interface to Ollama for local LLM inference.
"""

import httpx
import json
from typing import Optional, List, Dict, Any
from ..config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaClient:
    """Client for Ollama local LLM inference"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._client = httpx.AsyncClient(timeout=120.0)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate a response from the LLM"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self._client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            print(f"Ollama request failed: {e}")
            return f"Error: Could not connect to Ollama. Make sure it's running at {self.base_url}"
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Generate a JSON response from the LLM"""
        json_system = (system_prompt or "") + "\n\nIMPORTANT: Respond ONLY with valid JSON in this exact format. Start with { and end with }. No explanations, no markdown, no extra text."
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=json_system,
            temperature=temperature
        )
        
        # Try to extract JSON from the response
        try:
            clean_response = response.strip()
            
            # Remove markdown code blocks if present (handles ```json ... ```)
            if "```" in clean_response:
                # Find content between first ``` and last ```
                parts = clean_response.split("```")
                for part in parts:
                    part = part.strip()
                    # Skip empty parts and language identifiers
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{") or part.startswith("["):
                        clean_response = part
                        break
            
            # Try to find JSON object or array in the response
            if not (clean_response.startswith("{") or clean_response.startswith("[")):
                # Look for JSON object in the response
                start_brace = clean_response.find("{")
                start_bracket = clean_response.find("[")
                if start_brace >= 0:
                    end_brace = clean_response.rfind("}")
                    if end_brace > start_brace:
                        clean_response = clean_response[start_brace:end_brace+1]
                elif start_bracket >= 0:
                    end_bracket = clean_response.rfind("]")
                    if end_bracket > start_bracket:
                        clean_response = clean_response[start_bracket:end_bracket+1]
            
            return json.loads(clean_response.strip())
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response was: {response[:500]}")
            # Return empty dict to allow graceful degradation
            # The learning engine has a fallback for this
            return {}
    
    async def check_connection(self) -> bool:
        """Check if Ollama is running and the model is available"""
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return any(self.model in name for name in model_names)
            return False
        except:
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()


# Singleton instance
ollama_client = OllamaClient()
