"""
storage.py — Save results to CSV and JSON.
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any

import pandas as pd

logger = logging.getLogger("storage")


@dataclass
class ReviewResult:
    # Scraped metadata
    author: str
    rating: float | None
    date: str
    title: str
    url: str
    verified: bool
    # Cleaned review text
    review_text: str
    # LLM output
    sentiment: str
    sentiment_score: float | None
    summary: str
    key_themes: list[str] = field(default_factory=list)
    llm_fallback: bool = False


def save_results(results: list[ReviewResult], output_dir: str = "output") -> dict[str, str]:
    """
    Save results to output_dir as both CSV and JSON.
    Returns dict with file paths.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for r in results:
        d = asdict(r)
        d["key_themes"] = ", ".join(d.get("key_themes") or [])
        rows.append(d)

    # --- CSV ---
    csv_path = out / "reviews.csv"
    df = pd.DataFrame(rows)
    # Reorder columns for readability
    col_order = [
        "author", "rating", "date", "title", "sentiment", "sentiment_score",
        "summary", "key_themes", "verified", "review_text", "url", "llm_fallback"
    ]
    df = df[[c for c in col_order if c in df.columns]]
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved CSV → {csv_path}")

    # --- JSON ---
    json_path = out / "reviews.json"
    json_data = {
        "total": len(results),
        "reviews": [asdict(r) for r in results],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON → {json_path}")

    return {"csv": str(csv_path), "json": str(json_path)}


def print_summary(results: list[ReviewResult]) -> None:
    """Print a pretty console summary."""
    from collections import Counter

    if not results:
        print("No results to display.")
        return

    sentiments = Counter(r.sentiment for r in results)
    avg_rating = (
        sum(r.rating for r in results if r.rating is not None)
        / max(1, sum(1 for r in results if r.rating is not None))
    )

    print("\n" + "=" * 60)
    print(f"  REVIEW ANALYSIS SUMMARY  ({len(results)} reviews)")
    print("=" * 60)
    print(f"  Avg Rating   : {avg_rating:.1f} / 5.0")
    for sent, count in sorted(sentiments.items()):
        bar = "█" * count
        print(f"  {sent:<10} : {bar} ({count})")
    print("-" * 60)
    for i, r in enumerate(results, 1):
        stars = "★" * int(r.rating or 0) + "☆" * (5 - int(r.rating or 0))
        print(f"\n  [{i}] {r.author} | {stars} | {r.sentiment}")
        print(f"      {r.title}")
        print(f"      → {r.summary}")
        if r.key_themes:
            print(f"      Themes: {', '.join(r.key_themes)}")
    print("=" * 60 + "\n")
