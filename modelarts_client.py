"""
ModelArts Client for Huawei Cloud DeepSeek v3.1 Integration
Handles API calls to ModelArts Studio (MaaS) for LLM inference.
"""
import logging
import requests
import json
from typing import Optional, Dict, Any
from config import MODELARTS_ENDPOINT, DEEPSEEK_API_KEY, MODELARTS_MODEL_NAME, LLM_TEMPERATURE, LLM_MAX_TOKENS

logger = logging.getLogger(__name__)


class ModelArtsClient:
    """Client for interacting with Huawei Cloud ModelArts DeepSeek API."""
    
    def __init__(self):
        """Initialize ModelArts client."""
        self.endpoint = MODELARTS_ENDPOINT
        self.api_key = DEEPSEEK_API_KEY
        self.model_name = MODELARTS_MODEL_NAME or "deepseek-v3.1"
        
        if not self.endpoint or not self.api_key:
            logger.warning("ModelArts credentials not configured. ModelArts features disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"✅ ModelArts client initialized: {self.model_name}")
    
    def invoke_deepseek(
        self, 
        prompt: str, 
        temperature: float = None, 
        max_tokens: int = None,
        system_prompt: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke DeepSeek v3.1 model via ModelArts API.
        
        Args:
            prompt: User prompt/question
            temperature: Sampling temperature (default: from config)
            max_tokens: Maximum tokens to generate (default: from config)
            system_prompt: Optional system prompt
            
        Returns:
            API response dictionary or None if error
        """
        if not self.enabled:
            logger.error("ModelArts client not enabled")
            return None
        
        # Use config defaults if not provided
        temp = temperature if temperature is not None else LLM_TEMPERATURE
        max_toks = max_tokens if max_tokens is not None else LLM_MAX_TOKENS
        
        # Prepare API endpoint
        # ModelArts API format may vary - adjust based on actual API documentation
        url = f"{self.endpoint.rstrip('/')}/v1/chat/completions"
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare payload
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_toks,
            "stream": False
        }
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": self.api_key,
            # Alternative header formats (adjust based on actual API):
            # "Authorization": f"Bearer {self.api_key}",
            # "X-Api-Key": self.api_key,
        }
        
        try:
            logger.info(f"Calling ModelArts API: {url}")
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("✅ ModelArts API call successful")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ModelArts API request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"ModelArts API error: {e}")
            return None
    
    def extract_response_text(self, api_response: Dict[str, Any]) -> str:
        """
        Extract text response from ModelArts API response.
        
        Args:
            api_response: API response dictionary
            
        Returns:
            Extracted text response
        """
        if not api_response:
            return ""
        
        try:
            # ModelArts API response format may vary
            # Common formats:
            if "choices" in api_response and len(api_response["choices"]) > 0:
                choice = api_response["choices"][0]
                if "message" in choice:
                    return choice["message"].get("content", "")
                elif "text" in choice:
                    return choice["text"]
            
            # Fallback: try to find content in response
            if "content" in api_response:
                return api_response["content"]
            
            # If no standard format, return string representation
            logger.warning("Unexpected API response format")
            return str(api_response)
            
        except Exception as e:
            logger.error(f"Error extracting response text: {e}")
            return ""
    
    def is_available(self) -> bool:
        """Check if ModelArts client is available and configured."""
        return self.enabled

