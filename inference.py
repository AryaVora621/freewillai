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
        self.eval_model = os.getenv("OLLAMA_EVAL_MODEL", self.model)
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
                "keep_alive": -1,
                "options": {"num_predict": max_tokens}
            }
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=180)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            else:
                logger.error(f"Ollama error: {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ollama connection error: {e}")
            return None

    def generate_eval(self, prompt: str, max_tokens: int = 60) -> Optional[str]:
        """Generate using the faster local eval model (qwen2.5:0.5b if set)."""
        # Temporarily swap to eval_model for this call
        orig = self.model
        self.model = self.eval_model
        resp = self.generate(prompt, max_tokens=max_tokens)
        self.model = orig
        return resp

    def is_available(self) -> bool:
        """Check if Ollama has a usable model pulled"""
        return bool(self.available_models)

class OpenRouterClient:
    """Interface to OpenRouter cloud API"""

    # Free models that support structured/JSON output, in preference order
    FREE_MAIN_MODELS = [
        "openai/gpt-oss-120b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "nvidia/nemotron-3-8b-super:free",
        "google/gemma-3-27b-it:free",
        "qwen/qwen3-30b-a3b:free",
    ]
    FREE_CODE_MODELS = [
        "qwen/qwen3-coder:free",
        "openai/gpt-oss-120b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "nvidia/nemotron-3-8b-super:free",
    ]

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
        self.eval_model = os.getenv("OPENROUTER_EVAL_MODEL", self.model)
        self.code_model = os.getenv("OPENROUTER_CODE_MODEL", "qwen/qwen3-coder:free")
        self.base_url = "https://openrouter.ai/api/v1"
        self._rate_limited_models = set()

    def generate(self, prompt: str, max_tokens: int = 500, model: Optional[str] = None) -> Optional[str]:
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
                "model": model or self.model,
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
                    if attempt < 2:
                        time.sleep(wait)
                    continue
                logger.error(f"OpenRouter error: {resp.status_code} - {resp.text}")
                return None
            # All 3 attempts failed -- mark this model as rate-limited and try alternates
            active_model = model or self.model
            self._rate_limited_models.add(active_model)
            logger.error(f"OpenRouter rate-limited after retries, giving up on {active_model}")
            # Try a different model from the pool if available
            all_models = self.FREE_MAIN_MODELS + self.FREE_CODE_MODELS
            for alt in all_models:
                if alt not in self._rate_limited_models and alt != active_model:
                    logger.info(f"Trying alternate model: {alt}")
                    alt_payload = dict(payload)
                    alt_payload["model"] = alt
                    try:
                        alt_resp = requests.post(
                            f"{self.base_url}/chat/completions",
                            json=alt_payload, headers=headers, timeout=30
                        )
                        if alt_resp.status_code == 200:
                            return alt_resp.json()["choices"][0]["message"]["content"]
                    except Exception:
                        pass
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
            # Estimate prompt tokens (1 token ≈ 4 chars); skip local if too long for the timeout.
            # At ~4 tokens/sec (3B model), 400 tokens ≈ 100s — safe under 120s timeout.
            estimated_tokens = len(prompt) / 4
            if estimated_tokens <= 400:
                response = self.ollama.generate(prompt, max_tokens=max_tokens)
                # Quality gate: if local response is too short it likely failed or refused
                if response and len(response.strip()) >= 30:
                    return response
                if response:
                    logger.warning(f"Ollama response too short ({len(response.strip())} chars), trying OpenRouter")
                else:
                    logger.warning("Ollama failed, trying OpenRouter fallback")
            else:
                logger.info(f"Prompt ~{estimated_tokens:.0f} tokens — too long for local model, routing to OpenRouter")
            # Try OpenRouter as fallback / long-prompt primary
            if self.openrouter.is_available():
                response = self.openrouter.generate(prompt, max_tokens=max_tokens)
                if response:
                    logger.info("Switched to OpenRouter fallback")
                    return response

        # No backend available
        logger.error("✗ All inference backends exhausted")
        return None

    def generate_fast(self, prompt: str, max_tokens: int = 60) -> Optional[str]:
        """Fast eval: prefer local qwen2.5:0.5b, fall back to LFM (cloud), then default."""
        # Local eval model is fastest and uses no API quota
        if self.ollama.is_available():
            resp = self.ollama.generate_eval(prompt, max_tokens=max_tokens)
            if resp and len(resp.strip()) >= 5:
                return resp
        # Cloud LFM fallback
        if self.openrouter.is_available():
            resp = self.openrouter.generate(prompt, max_tokens=max_tokens, model=self.openrouter.eval_model)
            if resp:
                return resp
        return self.generate(prompt, max_tokens=max_tokens)

    def generate_code(self, prompt: str, max_tokens: int = 300) -> Optional[str]:
        """Use the code-specialized model (qwen3-coder) for code generation tasks."""
        if self.openrouter.is_available():
            resp = self.openrouter.generate(prompt, max_tokens=max_tokens, model=self.openrouter.code_model)
            if resp:
                return resp
        return self.generate(prompt, max_tokens=max_tokens)

    def get_active_model(self) -> str:
        """Get name of currently active model"""
        if self.active_backend == "ollama":
            return f"{self.ollama.model} (local)"
        elif self.active_backend == "openrouter":
            return f"{self.openrouter.model} (cloud)"
        else:
            return "none"
