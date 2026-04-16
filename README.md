# 🛍️ Product Review Scraper + LLM Analyser

A Python application that scrapes product reviews, preprocesses them, sends each to an LLM for sentiment analysis, and saves structured results to CSV and JSON.

---

## 📦 Tested URL

```
https://books.toscrape.com/
```

> **Why not Amazon?** Amazon (and Best Buy) aggressively block automated scrapers with CAPTCHAs, JavaScript rendering, and bot detection. The `--mock` flag provides 8 realistic reviews so you can fully demo and test the LLM pipeline without being blocked. The scraper *does* attempt real scraping for Amazon but falls back gracefully.

---

## 🗂️ Project Structure

```
review_scraper/
├── main.py           # CLI entry point & pipeline orchestrator
├── scraper.py        # Web scraping (Amazon, Best Buy, books.toscrape, generic)
├── mock_data.py      # 8 realistic mock reviews (headphones product)
├── preprocessor.py   # Text cleaning, unicode normalisation, chunking
├── llm_client.py     # OpenAI-compatible API client with retry/rate-limit logic
├── storage.py        # CSV + JSON output, console summary
├── requirements.txt  # Dependencies
└── output/           # Generated after running (CSV + JSON results)
```

---

## ⚙️ Setup

```bash
# 1. Clone / download the project
cd review_scraper

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Usage

### Option A — Mock data (recommended for testing, no site access needed)
```bash
python main.py --mock --api-key sk-YOUR_KEY_HERE
```

### Option B — Live scrape books.toscrape.com (bot-friendly demo site)
```bash
python main.py --url https://books.toscrape.com/ --api-key sk-YOUR_KEY_HERE
```

### Option C — Attempt Amazon scrape (may be blocked)
```bash
python main.py \
  --url "https://www.amazon.com/product-reviews/B08N5WRWNW" \
  --api-key sk-YOUR_KEY_HERE
```

### Option D — Skip LLM entirely (no API key, offline keyword fallback)
```bash
python main.py --mock --no-llm
```

### Option E — Use a local LLM (e.g. Ollama with llama3)
```bash
python main.py --mock \
  --base-url http://localhost:11434/v1 \
  --model llama3 \
  --api-key ollama
```

---

## 🔧 All CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | `https://books.toscrape.com/` | Product page URL |
| `--mock` | off | Use built-in mock reviews |
| `--api-key` | `$OPENAI_API_KEY` | OpenAI API key |
| `--base-url` | OpenAI's API | Base URL for any OpenAI-compatible API |
| `--model` | `gpt-3.5-turbo` | Model name |
| `--no-llm` | off | Use keyword fallback only |
| `--max-reviews` | 50 | Max reviews to process |
| `--output-dir` | `./output` | Where to save results |
| `--delay` | 1.0 | Seconds between LLM calls |

---

## 📊 Output Format

### `output/reviews.csv`
| Column | Description |
|--------|-------------|
| `author` | Reviewer name |
| `rating` | Star rating (1–5) |
| `date` | Review date |
| `title` | Review title |
| `sentiment` | Positive / Negative / Neutral / Mixed |
| `sentiment_score` | Confidence 0.0–1.0 |
| `summary` | LLM-generated 1–2 sentence summary |
| `key_themes` | Comma-separated theme keywords |
| `verified` | Verified purchase flag |
| `review_text` | Original cleaned review text |
| `url` | Source URL |
| `llm_fallback` | True if keyword fallback was used |

### `output/reviews.json`
Full structured JSON with all fields per review.

---

## 🛡️ Robustness Features

| Challenge | How It's Handled |
|-----------|-----------------|
| Bot detection / 403 | `--mock` flag + realistic user-agent rotation |
| Rate limits (429) | Exponential back-off with configurable retries |
| API failures | Retry loop + keyword-based fallback |
| Long reviews | Sliding-window chunking (300 token default) |
| Encoding issues | `unicodedata.normalize(NFKC)` + `apparent_encoding` |
| JSON parse errors | Safe fallback dict returned |
| Missing tiktoken | Character-based token estimator (≈4 chars/token) |

---

## 🔌 Compatible LLM Providers

Any OpenAI-compatible endpoint works:
- **OpenAI** — `gpt-3.5-turbo`, `gpt-4o`
- **Groq** — `llama3-8b-8192`
- **Together AI** — `mistralai/Mixtral-8x7B`
- **Ollama (local)** — `llama3`, `mistral`
- **Anthropic via proxy** — any compatible wrapper

---

## 📋 Example Console Output

```
============================================================
  REVIEW ANALYSIS SUMMARY  (8 reviews)
============================================================
  Avg Rating   : 3.6 / 5.0
  Positive     : ████ (4)
  Negative     : ██ (2)
  Mixed        : █ (1)
  Neutral      : █ (1)
------------------------------------------------------------

  [1] Sarah T. | ★★★★★ | Positive
      Absolutely love this product!
      → Customer praises easy setup, exceptional battery life, and clear sound quality.
      Themes: battery life, sound quality, ease of setup
...
============================================================
```
