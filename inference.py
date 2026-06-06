#!/usr/bin/env python3
"""
Hybrid inference layer - Ollama (local) with OpenRouter (cloud) fallback
"""

import os
import requests
import time
import logging
from typing import Optional
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaClient:
    """Interface to local Ollama for inference"""
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = os.getenv("OLLAMA_MODEL", "mistral")
        self.fallback_models = ["mistral", "neural-chat", "llama2-uncensored", "phi"]
        self.available_models = []
        self.check_available_models()

    def check_available_models(self):
        """Check which models are available locally"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                self.available_models = [m.get("name", "") for m in models]
                logger.info(f"Available Ollama models: {self.available_models}")

                # Switch to best available model if current one not available
                # Try exact match first, then prefix match (e.g. "llama3.2" matches "llama3.2:1b")
                if self.model not in self.available_models:
                    prefix_match = next((m for m in self.available_models if m.startswith(self.model.split(":")[0])), None)
                    if prefix_match:
                        self.model = prefix_match
                    elif self.available_models:
                        old_model = self.model
                        self.model = self.available_models[0]
                        logger.warning(f"Model {old_model} not available, switching to {self.model}")
        except Exception as e:
            logger.warning(f"Could not check available models: {e}")

    def generate(self, prompt: str, max_tokens: int = 400) -> Optional[str]:
        """Generate response from Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens}
            }
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            else:
                logger.error(f"Ollama error: {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ollama connection error: {e}")
            return None

    def is_available(self) -> bool:
        """Check if Ollama has a usable model pulled"""
        return bool(self.available_models)

class OpenRouterClient:
    """Interface to OpenRouter cloud API"""
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "nousresearch/nous-hermes-2-mistral-7b-dpo")
        self.base_url = "https://openrouter.ai/api/v1"

    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Generate response from OpenRouter"""
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/aryavora/freeWillAi",
                "X-Title": "freeWillAi"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": max_tokens
            }
            for attempt in range(3):
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                if resp.status_code == 429:
                    wait = 5
                    try:
                        wait = min(int(float(resp.json()["error"]["metadata"].get("retry_after_seconds", 5))) + 1, 20)
                    except Exception:
                        pass
                    logger.warning(f"OpenRouter rate-limited (attempt {attempt + 1}/3), waiting {wait}s")
                    time.sleep(wait)
                    continue
                logger.error(f"OpenRouter error: {resp.status_code} - {resp.text}")
                return None
            logger.error("OpenRouter rate-limited after retries, giving up")
            return None
        except Exception as e:
            logger.error(f"OpenRouter connection error: {e}")
            return None

    def is_available(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key)

class HybridInferenceEngine:
    """Use Ollama (local) with OpenRouter (cloud) fallback"""
    def __init__(self):
        self.ollama = OllamaClient()
        self.openrouter = OpenRouterClient()
        self.active_backend = None

        # Prefer local inference (genuine autonomy) when a model is available;
        # fall back to OpenRouter only when no local model is ready
        if self.ollama.is_available():
            self.active_backend = "ollama"
            logger.info(f"✓ Using Ollama ({self.ollama.model}) as primary backend — local-first")
        elif self.openrouter.is_available():
            self.active_backend = "openrouter"
            logger.info(f"✓ Using OpenRouter ({self.openrouter.model}) as primary backend (no local model)")
        else:
            logger.warning("✗ No inference backend available!")
            logger.warning("  Set OPENROUTER_API_KEY for cloud mode or install Ollama for local")
            self.active_backend = "none"

    def generate(self, prompt: str, max_tokens: int = 400) -> Optional[str]:
        """Generate response using best available backend with fallbacks"""

        # Try primary backend first
        if self.active_backend == "openrouter":
            response = self.openrouter.generate(prompt, max_tokens=max_tokens)
            if response:
                return response
            logger.warning("OpenRouter failed, trying Ollama fallback")
            # Try Ollama as fallback
            if self.ollama.is_available():
                response = self.ollama.generate(prompt, max_tokens=max_tokens)
                if response:
                    logger.info("Switched to Ollama fallback")
                    return response

        elif self.active_backend == "ollama":
            response = self.ollama.generate(prompt, max_tokens=max_tokens)
            # Quality gate: if local response is too short it likely failed or refused
            if response and len(response.strip()) >= 30:
                return response
            if response:
                logger.warning(f"Ollama response too short ({len(response.strip())} chars), trying OpenRouter")
            else:
                logger.warning("Ollama failed, trying OpenRouter fallback")
            # Try OpenRouter as fallback
            if self.openrouter.is_available():
                response = self.openrouter.generate(prompt, max_tokens=max_tokens)
                if response:
                    logger.info("Switched to OpenRouter fallback")
                    return response

        # No backend available
        logger.error("✗ All inference backends exhausted")
        return None

    def get_active_model(self) -> str:
        """Get name of currently active model"""
        if self.active_backend == "ollama":
            return f"{self.ollama.model} (local)"
        elif self.active_backend == "openrouter":
            return f"{self.openrouter.model} (cloud)"
        else:
            return "none"
