"""
llm_client.py — OpenAI-compatible API client with rate-limit handling.
"""

import time
import logging
import os
from typing import Optional

logger = logging.getLogger("llm_client")

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful product review analyst.
When given a customer review, respond with a JSON object containing:
  - "sentiment": one of "Positive", "Negative", "Neutral", or "Mixed"
  - "score": sentiment confidence from 0.0 to 1.0
  - "summary": a concise 1-2 sentence summary of the key points
  - "key_themes": a list of up to 3 short keyword phrases (e.g. ["battery life", "build quality"])

Respond ONLY with the raw JSON object. No markdown, no extra text."""

USER_TEMPLATE = "Review:\n\n{review_text}"


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        max_retries: int = 4,
        initial_backoff: float = 2.0,
    ):
        self.model = model
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff

        key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise ValueError(
                "No API key provided. Set OPENAI_API_KEY env var or pass --api-key."
            )

        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=key, base_url=base_url)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def analyse(self, review_text: str) -> dict:
        """
        Send review text to the LLM and return parsed analysis dict.
        Retries on rate-limit (429) and transient errors.
        """
        import json
        from openai import RateLimitError, APIError, APIConnectionError

        payload = USER_TEMPLATE.format(review_text=review_text[:3000])

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": payload},
                    ],
                    temperature=0.2,
                    max_tokens=300,
                )
                raw = resp.choices[0].message.content.strip()
                # Strip accidental markdown fences
                raw = raw.strip("```json").strip("```").strip()
                return json.loads(raw)

            except RateLimitError:
                wait = self.initial_backoff * (2 ** (attempt - 1))
                logger.warning(f"Rate limited. Waiting {wait:.0f}s (attempt {attempt}/{self.max_retries})")
                time.sleep(wait)

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}. Raw response: {raw!r}")
                return _fallback(review_text)

            except (APIError, APIConnectionError) as e:
                wait = self.initial_backoff * attempt
                logger.error(f"API error on attempt {attempt}: {e}. Retrying in {wait:.0f}s …")
                time.sleep(wait)

        logger.error("All retries exhausted. Returning fallback analysis.")
        return _fallback(review_text)


def _fallback(text: str) -> dict:
    """Basic keyword-based fallback when LLM is unavailable."""
    text_lower = text.lower()
    pos_words = {"great", "love", "excellent", "perfect", "amazing", "good", "best", "happy"}
    neg_words = {"bad", "terrible", "awful", "disappointed", "broken", "worst", "poor", "horrible"}
    pos = sum(1 for w in pos_words if w in text_lower)
    neg = sum(1 for w in neg_words if w in text_lower)
    if pos > neg:
        sentiment = "Positive"
    elif neg > pos:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
    return {
        "sentiment": sentiment,
        "score": round(max(pos, neg) / max(pos + neg, 1), 2),
        "summary": f"[Fallback] Review appears {sentiment.lower()} based on keyword analysis.",
        "key_themes": [],
        "_fallback": True,
    }
