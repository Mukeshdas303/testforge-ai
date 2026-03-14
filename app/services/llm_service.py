import httpx
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class OllamaLLMService:
    """
    Async client for Ollama's /api/generate endpoint.
    Uses phi3 by default (set in config).
    Handles streaming=False for clean single-response output.
    """

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model    = settings.ollama_model
        self.timeout  = settings.ollama_timeout

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Send a prompt to Ollama phi3 and return the full text response.
        Raises RuntimeError if Ollama is unreachable or returns an error.
        """
        payload = {
            "model":  self.model,
            "prompt": prompt,
            "stream": False,          # get everything in one JSON response
            "options": {
                "temperature": 0.3,   # lower = more deterministic/structured output
                "top_p": 0.9,
                "num_predict": 2048,
            }
        }

        # Prepend system context directly into the prompt for phi3
        # (phi3 chat template: <|system|>...<|end|><|user|>...<|end|><|assistant|>)
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()

            data = response.json()
            return data.get("response", "").strip()

        except httpx.ConnectError:
            raise RuntimeError(
                "Cannot reach Ollama. Make sure it is running: `ollama serve`"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Ping Ollama to verify it's alive."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False


# Singleton
llm_service = OllamaLLMService()