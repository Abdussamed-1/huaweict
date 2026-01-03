"""
LLM API Client for DeepSeek v3.1 and Qwen3-32B
Handles API calls to DeepSeek v3.1 via direct API or Huawei ModelArts.
Supports Qwen3-32B as alternative/fallback model via ModelArts.
All models use OpenAI-compatible API format.
"""
import logging
import requests
import json
from typing import Optional, Dict, Any
from config import (
    MODELARTS_ENDPOINT, DEEPSEEK_API_KEY, DEEPSEEK_API_BASE, 
    DEEPSEEK_MODEL_NAME, DEEPSEEK_USE_DIRECT_API,
    MODELARTS_MODEL_NAME, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    QWEN_ENABLED, QWEN_MODEL_NAME, QWEN_USE_AS_FALLBACK
)

logger = logging.getLogger(__name__)


class ModelArtsClient:
    """
    Client for interacting with Huawei ModelArts LLM APIs.
    Both DeepSeek-v3.1 and Qwen3-32B use the SAME endpoint and API key.
    Only the model name changes in the request body.
    
    Endpoint: https://api-ap-southeast-1.modelarts-maas.com/v1/chat/completions
    Models: deepseek-v3.1, qwen3-32b
    """
    
    def __init__(self):
        """Initialize LLM API client with primary and fallback models."""
        self.use_direct_api = DEEPSEEK_USE_DIRECT_API
        self.api_key = DEEPSEEK_API_KEY
        
        # Primary model configuration
        if self.use_direct_api:
            # Use direct DeepSeek API (api.deepseek.com)
            self.endpoint = f"{DEEPSEEK_API_BASE.rstrip('/')}/v1/chat/completions"
            self.model_name = DEEPSEEK_MODEL_NAME or "deepseek-chat"
            self.auth_header = "Authorization"
            self.auth_prefix = "Bearer "
            logger.info(f"✅ Using direct DeepSeek API: {self.endpoint}")
        else:
            # Use Huawei ModelArts (same endpoint for all models)
            self.endpoint = f"{MODELARTS_ENDPOINT.rstrip('/')}/v1/chat/completions"
            self.model_name = MODELARTS_MODEL_NAME or "deepseek-v3.1"
            self.auth_header = "X-Auth-Token"
            self.auth_prefix = ""  # No prefix for X-Auth-Token
            logger.info(f"✅ Using Huawei ModelArts: {self.endpoint}")
        
        if not self.api_key:
            logger.warning("API key not configured. LLM features disabled.")
            self.enabled = False
        elif not self.endpoint:
            logger.warning("Endpoint not configured. LLM features disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"✅ Primary model: {self.model_name}")
        
        # Qwen3-32B configuration (uses SAME endpoint and API key)
        self.qwen_enabled = QWEN_ENABLED
        self.qwen_use_as_fallback = QWEN_USE_AS_FALLBACK
        self.qwen_model_name = QWEN_MODEL_NAME or "qwen3-32b"
        
        if self.qwen_enabled:
            logger.info(f"✅ Qwen3-32B enabled: {self.qwen_model_name}")
            if self.qwen_use_as_fallback:
                logger.info("   → Configured as fallback when primary model fails")
        elif self.qwen_use_as_fallback and self.enabled:
            logger.info(f"✅ Qwen3-32B available as fallback: {self.qwen_model_name}")
    
    def invoke_deepseek(
        self, 
        prompt: str, 
        temperature: float = None, 
        max_tokens: int = None,
        system_prompt: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke primary model (DeepSeek v3.1) via API.
        
        Args:
            prompt: User prompt/question
            temperature: Sampling temperature (default: from config)
            max_tokens: Maximum tokens to generate (default: from config)
            system_prompt: Optional system prompt
            
        Returns:
            API response dictionary or None if error
        """
        if not self.enabled:
            logger.error("LLM API client not enabled")
            return None
        
        # Use config defaults if not provided
        temp = temperature if temperature is not None else LLM_TEMPERATURE
        max_toks = max_tokens if max_tokens is not None else LLM_MAX_TOKENS
        
        # Use the configured endpoint (already includes /v1/chat/completions)
        url = self.endpoint
        
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
            "Content-Type": "application/json",
            self.auth_header: f"{self.auth_prefix}{self.api_key}"
        }
        
        try:
            logger.info(f"Calling API: {url}")
            logger.debug(f"Model: {self.model_name}, Temperature: {temp}, Max Tokens: {max_toks}")
            
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ {self.model_name} API call successful")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.model_name} API request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            
            # Try Qwen3-32B fallback if enabled (same endpoint, different model)
            if self.qwen_enabled and self.qwen_use_as_fallback:
                logger.info("Attempting Qwen3-32B fallback...")
                return self._invoke_qwen(prompt, temp, max_toks, system_prompt)
            return None
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            # Try Qwen3-32B fallback if enabled
            if self.qwen_use_as_fallback:
                logger.info("Attempting Qwen3-32B fallback...")
                return self._invoke_qwen(prompt, temp, max_toks, system_prompt)
            return None
    
    def _invoke_qwen(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke Qwen3-32B model via Huawei ModelArts.
        Uses the SAME endpoint and API key as DeepSeek, only model name changes.
        
        Args:
            prompt: User prompt/question
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Returns:
            API response dictionary or None if error
        """
        if not self.enabled:
            logger.error("LLM API client not enabled")
            return None
        
        # Use the SAME endpoint as primary model
        url = self.endpoint
        
        # Prepare messages (OpenAI-compatible format)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare payload - only model name changes to qwen3-32b
        payload = {
            "model": self.qwen_model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        # Use the SAME authentication as primary model
        headers = {
            "Content-Type": "application/json",
            self.auth_header: f"{self.auth_prefix}{self.api_key}"
        }
        
        try:
            logger.info(f"Calling Qwen3-32B API: {url}")
            logger.debug(f"Model: {self.qwen_model_name}, Temperature: {temperature}, Max Tokens: {max_tokens}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=90  # Qwen may need more time
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("✅ Qwen3-32B API call successful")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Qwen3-32B API request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Qwen3-32B API error: {e}")
            return None
    
    def invoke_qwen(
        self,
        prompt: str,
        temperature: float = None,
        max_tokens: int = None,
        system_prompt: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Explicitly invoke Qwen3-32B model (public method).
        Use this when you want to use Qwen3-32B directly instead of DeepSeek.
        
        Args:
            prompt: User prompt/question
            temperature: Sampling temperature (default: from config)
            max_tokens: Maximum tokens to generate (default: from config)
            system_prompt: Optional system prompt
            
        Returns:
            API response dictionary or None if error
        """
        temp = temperature if temperature is not None else LLM_TEMPERATURE
        max_toks = max_tokens if max_tokens is not None else LLM_MAX_TOKENS
        return self._invoke_qwen(prompt, temp, max_toks, system_prompt)
    
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
        """Check if primary LLM API client is available and configured."""
        return self.enabled
    
    def is_qwen_available(self) -> bool:
        """Check if Qwen3-32B is available (uses same endpoint as primary)."""
        return self.enabled  # Same endpoint, so if primary works, Qwen works too
    
    def get_available_models(self) -> list:
        """Get list of available models."""
        models = []
        if self.enabled:
            models.append({
                "name": self.model_name,
                "type": "primary",
                "provider": "DeepSeek API" if self.use_direct_api else "Huawei ModelArts"
            })
            # Qwen uses same endpoint, always available if primary is available
            models.append({
                "name": self.qwen_model_name,
                "type": "primary" if self.qwen_enabled else "fallback",
                "provider": "Huawei ModelArts"
            })
        return models

