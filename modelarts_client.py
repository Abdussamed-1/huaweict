"""
LLM API Client for DeepSeek v3.1 and Qwen3-32B
Handles API calls to DeepSeek v3.1 via direct API or Huawei ModelArts.
Supports Qwen3-32B as alternative/fallback model via ModelArts.
All models use OpenAI-compatible API format.

Working Postman Response Format:
{
    "id": "chat-xxx",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "deepseek-v3.1",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "response text",
                "reasoning_content": null,
                "tool_calls": []
            },
            "logprobs": null,
            "finish_reason": "stop",
            "stop_reason": null
        }
    ],
    "usage": {
        "prompt_tokens": 13,
        "total_tokens": 15,
        "completion_tokens": 2
    }
}
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
            self.auth_header = "Authorization"
            self.auth_prefix = "Bearer "  # Use Bearer token format like Postman
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
        
        Request format (matching working Postman):
        POST /v1/chat/completions
        Headers:
            Content-Type: application/json
            Authorization: Bearer <api_key>
        Body:
            {
                "model": "deepseek-v3.1",
                "messages": [{"role": "user", "content": "..."}]
            }
        
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
        
        # Prepare payload - matching Postman working format
        payload = {
            "model": self.model_name,
            "messages": messages
        }
        
        # Add optional parameters only if specified (Postman might not send these)
        if temp is not None and temp != 0.2:  # Only add if not default
            payload["temperature"] = temp
        if max_toks is not None and max_toks != 2048:  # Only add if not default
            payload["max_tokens"] = max_toks
        
        # Prepare headers - using Authorization: Bearer format (matching Postman)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            logger.info(f"Calling API: {url}")
            logger.info(f"Model: {self.model_name}")
            logger.debug(f"Payload: {json.dumps(payload, ensure_ascii=False)[:500]}")
            
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=120  # Increased timeout for longer responses
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Log response info (matching Postman response structure)
            if "id" in result:
                logger.info(f"✅ API Response ID: {result.get('id')}")
            if "usage" in result:
                usage = result["usage"]
                logger.info(f"✅ Tokens - Prompt: {usage.get('prompt_tokens')}, Completion: {usage.get('completion_tokens')}, Total: {usage.get('total_tokens')}")
            
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
        
        Request format (same as DeepSeek):
        POST /v1/chat/completions
        Headers:
            Content-Type: application/json
            Authorization: Bearer <api_key>
        Body:
            {
                "model": "qwen3-32b",
                "messages": [{"role": "user", "content": "..."}]
            }
        
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
        
        # Prepare payload - matching Postman format, only model name changes
        payload = {
            "model": self.qwen_model_name,
            "messages": messages
        }
        
        # Add optional parameters only if not default values
        if temperature is not None and temperature != 0.2:
            payload["temperature"] = temperature
        if max_tokens is not None and max_tokens != 2048:
            payload["max_tokens"] = max_tokens
        
        # Use Authorization: Bearer format (matching Postman)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            logger.info(f"Calling Qwen3-32B API: {url}")
            logger.info(f"Model: {self.qwen_model_name}")
            logger.debug(f"Payload: {json.dumps(payload, ensure_ascii=False)[:500]}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120  # Increased timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Log response info (matching Postman response structure)
            if "id" in result:
                logger.info(f"✅ API Response ID: {result.get('id')}")
            if "usage" in result:
                usage = result["usage"]
                logger.info(f"✅ Tokens - Prompt: {usage.get('prompt_tokens')}, Completion: {usage.get('completion_tokens')}, Total: {usage.get('total_tokens')}")
            
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
        Extract text response from API response.
        
        Expected Postman response format:
        {
            "id": "chat-xxx",
            "object": "chat.completion",
            "model": "deepseek-v3.1",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "response text",
                        "reasoning_content": null,
                        "tool_calls": []
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {...}
        }
        
        Args:
            api_response: API response dictionary
            
        Returns:
            Extracted text response
        """
        if not api_response:
            return ""
        
        try:
            # Primary format: choices[0].message.content (matching Postman)
            if "choices" in api_response and len(api_response["choices"]) > 0:
                choice = api_response["choices"][0]
                
                # Standard message format
                if "message" in choice:
                    message = choice["message"]
                    content = message.get("content", "")
                    
                    # Log reasoning_content if available (DeepSeek feature)
                    reasoning = message.get("reasoning_content")
                    if reasoning:
                        logger.debug(f"Reasoning content available: {reasoning[:200]}...")
                    
                    if content:
                        return content
                
                # Legacy text format
                elif "text" in choice:
                    return choice["text"]
                
                # Streaming format
                elif "delta" in choice and "content" in choice["delta"]:
                    return choice["delta"]["content"]
            
            # Fallback: direct content field
            if "content" in api_response:
                return api_response["content"]
            
            # Log unexpected format
            logger.warning(f"Unexpected API response format: {list(api_response.keys())}")
            logger.debug(f"Full response: {json.dumps(api_response, ensure_ascii=False)[:500]}")
            return str(api_response)
            
        except Exception as e:
            logger.error(f"Error extracting response text: {e}")
            logger.debug(f"Raw response: {api_response}")
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

