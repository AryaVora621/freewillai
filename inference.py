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
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        # smollm2:135m is fast (~0.1s) for eval; qwen2.5:0.5b is fallback
        self.eval_model = os.getenv("OLLAMA_EVAL_MODEL", "smollm2:135m")
        self.fallback_models = ["llama3.2:1b", "qwen2.5:0.5b", "smollm2:135m"]
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
                # Auto-select fastest available eval model
                FAST_EVAL_MODELS = ["smollm2:135m", "qwen2.5:0.5b"]
                if self.eval_model not in self.available_models:
                    for fast in FAST_EVAL_MODELS:
                        if fast in self.available_models:
                            self.eval_model = fast
                            logger.info(f"Using {fast} as eval model")
                            break
                    else:
                        self.eval_model = self.model  # fallback to main model
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
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            else:
                logger.error(f"Ollama error: {resp.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.warning("Ollama timeout — killing background inference process to reclaim CPU")
            try:
                import subprocess as _sp
                _sp.run(['pkill', '-f', 'ollama runner'], capture_output=True, timeout=2)
            except Exception:
                pass
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
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "moonshotai/kimi-k2.6:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "openai/gpt-oss-120b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "qwen/qwen3-30b-a3b:free",
    ]
    FREE_CODE_MODELS = [
        "openai/gpt-oss-120b:free",
        "moonshotai/kimi-k2.6:free",
        "meta-llama/llama-3.3-70b-instruct:free",
    ]
    # These models return prose instead of code even with system prompts -- skip for code tasks
    PROSE_ONLY_MODELS = {
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "qwen/qwen3-coder-turbo:free",  # returning 404
        "qwen/qwen3-30b-a3b:free",      # returning 404
    }

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
        self.eval_model = os.getenv("OPENROUTER_EVAL_MODEL", self.model)
        self.code_model = os.getenv("OPENROUTER_CODE_MODEL", "openai/gpt-oss-120b:free")
        self.base_url = "https://openrouter.ai/api/v1"
        self._rate_limited_models = set()
        # Simple in-memory LRU cache: (prompt_hash, model) -> response
        # Avoids duplicate API calls when the same prompt fires in quick succession
        self._response_cache: dict = {}
        self._cache_order: list = []
        self._cache_max = 10
        # Rate limiter: track call timestamps to proactively space requests
        # OpenRouter free tier: ~10 req/min per model; stay under with 6s min gap
        self._call_times: list = []
        self._min_gap_s = float(os.getenv("OPENROUTER_MIN_GAP_S", "4"))

    def _cache_key(self, prompt: str, model: str) -> str:
        import hashlib
        return hashlib.md5((prompt[:500] + model).encode()).hexdigest()

    def generate(self, prompt: str, max_tokens: int = 500, model: Optional[str] = None, system: Optional[str] = None, allow_fallback: bool = True) -> Optional[str]:
        """Generate response from OpenRouter"""
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set")
            return None

        # Cache hit -- skip API call for identical prompts
        active_model = model or self.model
        cache_key = self._cache_key(prompt + (system or ""), active_model)
        if cache_key in self._response_cache:
            logger.debug("OpenRouter cache hit")
            return self._response_cache[cache_key]

        # Proactive rate limiter: ensure min gap between calls
        now = time.time()
        self._call_times = [t for t in self._call_times if now - t < 60]
        if self._call_times and (now - self._call_times[-1]) < self._min_gap_s:
            wait = self._min_gap_s - (now - self._call_times[-1])
            logger.debug(f"Rate limiter: sleeping {wait:.1f}s")
            time.sleep(wait)
        self._call_times.append(time.time())

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/aryavora/freeWillAi",
                "X-Title": "freeWillAi"
            }
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            payload = {
                "model": model or self.model,
                "messages": messages,
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
                    content = resp.json()["choices"][0]["message"]["content"]
                    # Store in LRU cache (evict oldest if full)
                    if len(self._cache_order) >= self._cache_max:
                        old_key = self._cache_order.pop(0)
                        self._response_cache.pop(old_key, None)
                    self._response_cache[cache_key] = content
                    self._cache_order.append(cache_key)
                    return content
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
                if resp.status_code == 404:
                    # Model deprecated or not found — skip immediately, no retries
                    logger.warning(f"OpenRouter 404 (deprecated/missing): {(model or self.model)}")
                    break
                logger.error(f"OpenRouter error: {resp.status_code} - {resp.text}")
                return None
            # All 3 attempts failed -- mark this model as rate-limited and try alternates
            active_model = model or self.model
            self._rate_limited_models.add(active_model)
            logger.error(f"OpenRouter rate-limited after retries, giving up on {active_model}")
            if not allow_fallback:
                return None
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

        # Honor INFERENCE_BACKEND env: "local-first" or "cloud-first" (default)
        backend_pref = os.getenv("INFERENCE_BACKEND", "cloud-first").lower()

        if backend_pref == "local-first" and self.ollama.is_available():
            self.active_backend = "ollama"
            logger.info(f"✓ Using Ollama ({self.ollama.model}) as primary backend (local-first mode)")
        elif self.openrouter.is_available():
            self.active_backend = "openrouter"
            logger.info(f"✓ Using OpenRouter ({self.openrouter.model}) as primary backend (cloud-first mode)")
        elif self.ollama.is_available():
            self.active_backend = "ollama"
            logger.info(f"✓ Using Ollama ({self.ollama.model}) as primary backend (no cloud API key)")
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
            max_prompt_tokens = int(os.getenv("OLLAMA_MAX_PROMPT_TOKENS", "400"))
            if estimated_tokens <= max_prompt_tokens:
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

    def generate_code(self, prompt: str, max_tokens: int = 300, system: Optional[str] = None) -> Optional[str]:
        """Use code-safe models only (never nemotron/prose-only models).
        Manages its own fallback so generate() doesn't silently fall back to bad models.
        """
        # In local-first mode, try local code model first
        backend_pref = os.getenv("INFERENCE_BACKEND", "cloud-first").lower()
        if backend_pref == "local-first" and self.ollama.is_available():
            code_model = os.getenv("OLLAMA_CODE_MODEL", self.ollama.model)
            logger.debug(f"Code gen: trying local model {code_model}")
            resp = self.ollama.generate(prompt, max_tokens=max_tokens)
            if resp and len(resp.strip()) >= 20:
                return resp
            logger.warning("Local code model failed, falling back to OpenRouter")

        if not self.openrouter.is_available():
            return None
        or_client = self.openrouter
        # Try each code-safe model in priority order; skip prose-only and rate-limited
        candidates = [or_client.code_model] + [
            m for m in or_client.FREE_CODE_MODELS
            if m != or_client.code_model and m not in or_client.PROSE_ONLY_MODELS
        ]
        for model_id in candidates:
            if model_id in or_client.PROSE_ONLY_MODELS or model_id in or_client._rate_limited_models:
                continue
            logger.debug(f"Code gen: trying {model_id}")
            resp = or_client.generate(prompt, max_tokens=max_tokens, model=model_id,
                                      system=system, allow_fallback=False)
            if resp:
                return resp
        return None

    def get_active_model(self) -> str:
        """Get name of currently active model"""
        if self.active_backend == "ollama":
            return f"{self.ollama.model} (local)"
        elif self.active_backend == "openrouter":
            return f"{self.openrouter.model} (cloud)"
        else:
            return "none"
