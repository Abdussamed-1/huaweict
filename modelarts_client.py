"""
DeepSeek v3.1 API Client
Handles API calls to DeepSeek v3.1 via direct API or Huawei ModelArts.
Supports OpenAI-compatible API format.
"""
import logging
import requests
import json
from typing import Optional, Dict, Any
from config import (
    MODELARTS_ENDPOINT, DEEPSEEK_API_KEY, DEEPSEEK_API_BASE, 
    DEEPSEEK_MODEL_NAME, DEEPSEEK_USE_DIRECT_API,
    MODELARTS_MODEL_NAME, LLM_TEMPERATURE, LLM_MAX_TOKENS
)

logger = logging.getLogger(__name__)


class ModelArtsClient:
    """
    Client for interacting with DeepSeek v3.1 API.
    Supports both direct DeepSeek API and Huawei ModelArts integration.
    """
    
    def __init__(self):
        """Initialize DeepSeek API client."""
        self.use_direct_api = DEEPSEEK_USE_DIRECT_API
        self.api_key = DEEPSEEK_API_KEY
        
        if self.use_direct_api:
            # Use direct DeepSeek API
            self.endpoint = f"{DEEPSEEK_API_BASE.rstrip('/')}/v1/chat/completions"
            self.model_name = DEEPSEEK_MODEL_NAME or "deepseek-chat"
            self.auth_header = "Authorization"
            logger.info(f"✅ Using direct DeepSeek API: {self.endpoint}")
        else:
            # Use Huawei ModelArts
            self.endpoint = MODELARTS_ENDPOINT
            self.model_name = MODELARTS_MODEL_NAME or "deepseek-v3.1"
            self.auth_header = "X-Auth-Token"
            logger.info(f"✅ Using Huawei ModelArts: {self.endpoint}")
        
        if not self.api_key:
            logger.warning("DeepSeek API key not configured. DeepSeek features disabled.")
            self.enabled = False
        elif not self.use_direct_api and not self.endpoint:
            logger.warning("ModelArts endpoint not configured. DeepSeek features disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"✅ DeepSeek client initialized: {self.model_name}")
    
    def invoke_deepseek(
        self, 
        prompt: str, 
        temperature: float = None, 
        max_tokens: int = None,
        system_prompt: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke DeepSeek v3.1 model via API (direct or ModelArts).
        
        Args:
            prompt: User prompt/question
            temperature: Sampling temperature (default: from config)
            max_tokens: Maximum tokens to generate (default: from config)
            system_prompt: Optional system prompt
            
        Returns:
            API response dictionary or None if error
        """
        if not self.enabled:
            logger.error("DeepSeek API client not enabled")
            return None
        
        # Use config defaults if not provided
        temp = temperature if temperature is not None else LLM_TEMPERATURE
        max_toks = max_tokens if max_tokens is not None else LLM_MAX_TOKENS
        
        # Prepare API endpoint
        if self.use_direct_api:
            # Direct DeepSeek API endpoint
            url = self.endpoint
        else:
            # Huawei ModelArts endpoint
            url = f"{self.endpoint.rstrip('/')}/v1/chat/completions"
        
        # Prepare messages (OpenAI-compatible format)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare payload (OpenAI-compatible format)
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_toks,
            "stream": False
        }
        
        # Prepare headers based on API type
        headers = {
            "Content-Type": "application/json"
        }
        
        # Set authentication header
        if self.use_direct_api:
            # Direct DeepSeek API uses Bearer token
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            # Huawei ModelArts uses X-Auth-Token
            headers["X-Auth-Token"] = self.api_key
        
        try:
            logger.info(f"Calling DeepSeek API: {url}")
            logger.debug(f"Model: {self.model_name}, Temperature: {temp}, Max Tokens: {max_toks}")
            
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("✅ DeepSeek API call successful")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return None
    
    def extract_response_text(self, api_response: Dict[str, Any]) -> str:
        """
        Extract text response from DeepSeek API response (OpenAI-compatible format).
        
        Args:
            api_response: API response dictionary
            
        Returns:
            Extracted text response
        """
        if not api_response:
            return ""
        
        try:
            # OpenAI-compatible response format
            if "choices" in api_response and len(api_response["choices"]) > 0:
                choice = api_response["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
                    if content:
                        return content
                elif "text" in choice:
                    return choice["text"]
                elif "delta" in choice and "content" in choice["delta"]:
                    # Streaming response format
                    return choice["delta"]["content"]
            
            # Fallback: try to find content in response
            if "content" in api_response:
                return api_response["content"]
            
            # If no standard format, log warning and return string representation
            logger.warning(f"Unexpected API response format: {list(api_response.keys())}")
            return str(api_response)
            
        except Exception as e:
            logger.error(f"Error extracting response text: {e}")
            return ""
    
    def is_available(self) -> bool:
        """Check if DeepSeek API client is available and configured."""
        return self.enabled

