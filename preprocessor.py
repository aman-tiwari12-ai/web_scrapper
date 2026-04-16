"""
preprocessor.py — Clean and chunk review text for LLM input.
"""

import re
import unicodedata
import logging

logger = logging.getLogger("preprocessor")

# Rough token estimator (≈ 4 chars per token) used when tiktoken is unavailable
_CHARS_PER_TOKEN = 4

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_ENC.encode(text))

except ImportError:
    logger.warning("tiktoken not installed — using character-based token estimate.")

    def count_tokens(text: str) -> int:  # type: ignore[misc]
        return max(1, len(text) // _CHARS_PER_TOKEN)


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Normalize encoding, strip HTML artefacts, collapse whitespace."""
    # Normalize unicode (handles mojibake-style issues)
    text = unicodedata.normalize("NFKC", text)

    # Remove HTML entities that may have slipped through
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)

    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # Remove repeated punctuation (e.g., "!!!!!!")
    text = re.sub(r"([!?.]){3,}", r"\1", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ---------------------------------------------------------------------------
# Chunking (for long reviews)
# ---------------------------------------------------------------------------

def chunk_text(text: str, max_tokens: int = 300, overlap: int = 30) -> list[str]:
    """
    Split text into chunks of ≤ max_tokens with overlap between chunks.
    Returns a list of text chunks (usually just one for normal reviews).
    """
    if count_tokens(text) <= max_tokens:
        return [text]

    words = text.split()
    chunks: list[str] = []
    start = 0

    while start < len(words):
        chunk_words: list[str] = []
        tokens = 0
        i = start
        while i < len(words):
            word_tokens = count_tokens(words[i] + " ")
            if tokens + word_tokens > max_tokens:
                break
            chunk_words.append(words[i])
            tokens += word_tokens
            i += 1

        if not chunk_words:
            # Single word exceeds max — force include it
            chunk_words = [words[start]]
            i = start + 1

        chunks.append(" ".join(chunk_words))
        next_start = i - overlap
        start = max(start + 1, next_start)  # always advance

    logger.debug(f"Long review split into {len(chunks)} chunks.")
    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def preprocess(text: str, max_tokens: int = 300) -> list[str]:
    """Clean and chunk a review. Returns list of text chunks."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    return chunk_text(cleaned, max_tokens=max_tokens)
