"""
mock_data.py — Realistic mock reviews for testing without live scraping.
Used when --mock flag is passed or when live scraping is blocked.
"""

from scraper import Review

MOCK_REVIEWS: list[Review] = [
    Review(
        author="Sarah T.",
        rating=5.0,
        date="March 12, 2024",
        title="Absolutely love this product!",
        text=(
            "This is hands down the best purchase I've made this year. "
            "Setup was a breeze — took me under 10 minutes. The battery life "
            "is incredible; I've been using it daily for two weeks and only "
            "charged it once. Sound quality is crisp and clear with deep bass. "
            "Highly recommend to anyone on the fence."
        ),
        verified=True,
    ),
    Review(
        author="Mike R.",
        rating=2.0,
        date="February 28, 2024",
        title="Disappointed with build quality",
        text=(
            "I had high hopes based on the reviews but the plastic casing feels "
            "very cheap. After three weeks of normal use, the charging port became "
            "loose. Customer service was unresponsive for five days. The sound is "
            "decent but not worth the price given these quality issues. Returning it."
        ),
        verified=True,
    ),
    Review(
        author="Priya M.",
        rating=4.0,
        date="March 3, 2024",
        title="Great value, minor software quirks",
        text=(
            "Overall I'm very happy with this. The hardware is solid and the "
            "performance exceeds what I expected at this price point. My only "
            "gripe is the companion app crashes occasionally on Android 14. "
            "I'm sure a firmware update will fix it. The noise cancellation is "
            "impressive — perfect for my open-plan office."
        ),
        verified=True,
    ),
    Review(
        author="James K.",
        rating=1.0,
        date="January 15, 2024",
        title="Stopped working after 2 weeks",
        text=(
            "Do NOT buy this. Mine died completely after exactly 14 days. Would "
            "not turn on, charge, or respond to resets. The warranty process is "
            "a nightmare — they keep asking for proof of purchase even though I "
            "ordered directly from their website. Worst post-purchase experience ever."
        ),
        verified=False,
    ),
    Review(
        author="Linda H.",
        rating=5.0,
        date="March 18, 2024",
        title="Perfect gift, fast shipping",
        text=(
            "Bought this as a birthday gift for my husband and he absolutely loves it. "
            "Arrived two days early, packaging was premium and undamaged. He says the "
            "sound profile is warm and balanced, which is exactly what he wanted for "
            "jazz and classical music. Will definitely buy from this brand again."
        ),
        verified=True,
    ),
    Review(
        author="Carlos V.",
        rating=3.0,
        date="March 5, 2024",
        title="Average — does what it says, nothing more",
        text=(
            "It's fine. Does exactly what it advertises. Neither impressed nor "
            "disappointed. Battery is as advertised (about 20 hours). Sound is "
            "okay — nothing special compared to competitors at the same price. "
            "If you need something basic and reliable this will do. If you want "
            "to be wowed, look elsewhere."
        ),
        verified=True,
    ),
    Review(
        author="Aisha B.",
        rating=4.0,
        date="February 10, 2024",
        title="Comfortable for long sessions",
        text=(
            "I wear these for 6-8 hours a day during work calls and gaming sessions. "
            "The ear cups are incredibly comfortable — no soreness even after extended "
            "wear. Microphone clarity is excellent; colleagues have commented on how "
            "clear I sound. Slight downside: gets warm in summer. Still a 4-star "
            "product without question."
        ),
        verified=True,
    ),
    Review(
        author="Tom W.",
        rating=5.0,
        date="March 22, 2024",
        title="Exceeded all expectations",
        text=(
            "I'm an audiophile and was skeptical given the price. But this blew me "
            "away. The soundstage is wide, instrument separation is excellent, and "
            "the low end is tight without being muddy. Pairs beautifully with my DAC. "
            "Build quality is premium — metal hinges, quality foam. This is a "
            "serious product at a mid-range price. Five stars without hesitation."
        ),
        verified=True,
    ),
]


def get_mock_reviews(url: str = "https://mock-product-url.example.com/headphones") -> list[Review]:
    """Return mock reviews with the URL attached."""
    for r in MOCK_REVIEWS:
        r.url = url
    return MOCK_REVIEWS
