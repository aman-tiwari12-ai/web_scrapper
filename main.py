

import argparse
import logging
import time
import sys
from dataclasses import asdict

from scraper import scrape_reviews, Review
from mock_data import get_mock_reviews
from preprocessor import preprocess
from llm_client import LLMClient, _fallback
from storage import ReviewResult, save_results, print_summary



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")




def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape product reviews and analyse them with an LLM."
    )
    p.add_argument(
        "--url",
        default="https://books.toscrape.com/",
        help="Product page URL to scrape (default: books.toscrape.com demo)",
    )
    p.add_argument(
        "--mock",
        action="store_true",
        help="Use built-in mock reviews instead of live scraping",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
    )
    p.add_argument(
        "--base-url",
        default="https://api.openai.com/v1",
        help="Base URL for OpenAI-compatible API",
    )
    p.add_argument(
        "--model",
        default="gpt-3.5-turbo",
        help="Model name to use (default: gpt-3.5-turbo)",
    )
    p.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM calls; use keyword-based fallback only",
    )
    p.add_argument(
        "--max-reviews",
        type=int,
        default=50,
        help="Maximum number of reviews to process (default: 50)",
    )
    p.add_argument(
        "--output-dir",
        default="output",
        help="Directory for output files (default: ./output)",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between LLM calls (default: 1.0)",
    )
    return p.parse_args()



def run(args: argparse.Namespace) -> None:

    if args.mock:
        logger.info("Using mock review data.")
        reviews: list[Review] = get_mock_reviews(url=args.url)
    else:
        logger.info(f"Scraping: {args.url}")
        reviews = scrape_reviews(args.url)
        if not reviews:
            logger.error("No reviews were found. Check the URL or try --mock.")
            sys.exit(1)

    reviews = reviews[: args.max_reviews]
    logger.info(f"Processing {len(reviews)} reviews …")

    llm: LLMClient | None = None
    if not args.no_llm:
        try:
            llm = LLMClient(
                api_key=args.api_key,
                base_url=args.base_url,
                model=args.model,
            )
            logger.info(f"LLM client ready: {args.model} @ {args.base_url}")
        except (ValueError, ImportError) as e:
            logger.warning(f"LLM unavailable ({e}). Falling back to keyword analysis.")

    results: list[ReviewResult] = []

    for idx, review in enumerate(reviews, 1):
        preview = (review.title or review.text[:40]) + "..."
        logger.info(f"Analysing review {idx}/{len(reviews)}: \"{preview}\"")

        # Preprocess
        chunks = preprocess(review.text, max_tokens=300)
        if not chunks:
            logger.warning(f"Review {idx} had no usable text after preprocessing. Skipping.")
            continue

        text_for_llm = chunks[0]
        if len(chunks) > 1:
            logger.info(f"  Review split into {len(chunks)} chunks; using chunk 1.")

       
        if llm:
            analysis = llm.analyse(text_for_llm)
            time.sleep(args.delay)  # polite rate limiting
        else:
            analysis = _fallback(text_for_llm)

        results.append(ReviewResult(
            author=review.author,
            rating=review.rating,
            date=review.date,
            title=review.title,
            url=review.url,
            verified=review.verified,
            review_text=review.text,
            sentiment=analysis.get("sentiment", "Neutral"),
            sentiment_score=analysis.get("score"),
            summary=analysis.get("summary", ""),
            key_themes=analysis.get("key_themes", []),
            llm_fallback=bool(analysis.get("_fallback")),
        ))

    if not results:
        logger.error("No results to save.")
        sys.exit(1)

  
    paths = save_results(results, output_dir=args.output_dir)
    print_summary(results)
    logger.info(f"Done! Files saved:")
    logger.info(f"  CSV  → {paths['csv']}")
    logger.info(f"  JSON → {paths['json']}")



if __name__ == "__main__":
    run(parse_args())
