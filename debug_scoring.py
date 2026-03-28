# debug_scoring.py — One-time debug script
import sys
sys.path.insert(0, '.')

from scraper import scrape_posts
from scorer import score_post, get_recency_bonus
from config import GAP_SIGNALS, TECH_SIGNALS
from logger import init_db, load_replied_posts

def debug_score(post):
    """Return detailed score breakdown."""
    text = post["text"].lower()

    # Keyword match (0.30)
    keyword_hits = sum(1 for kw in TECH_SIGNALS if kw.lower() in text)
    keyword_score = min(keyword_hits / len(TECH_SIGNALS), 1.0) * 0.30

    # Engagement (0.25)
    likes = post.get("like_count", 0)
    reposts = post.get("repost_count", 0)
    replies = post.get("reply_count", 0)
    engagement = likes + (reposts * 2) + replies
    engagement_score = min(engagement / 500, 1.0) * 0.25

    # Tech depth (0.20)
    tech_hits = sum(1 for sig in TECH_SIGNALS if sig.lower() in text)
    tech_score = min(tech_hits / 5, 1.0) * 0.20

    # Gap signal (0.15)
    gap_hits = sum(1 for sig in GAP_SIGNALS if sig.lower() in text)
    gap_score = min(gap_hits / 3, 1.0) * 0.15

    # Author (0.10)
    author = post.get("author", "").lower()
    relevance_signals = ["ai", "agent", "ml", "engineer", "researcher", "dev", "build"]
    author_hits = sum(1 for sig in relevance_signals if sig in author)
    author_score = min(author_hits / 2, 1.0) * 0.10

    # Recency
    recency = get_recency_bonus(post.get("created_at", ""))

    total = keyword_score + engagement_score + tech_score + gap_score + author_score + recency
    total = max(0.0, min(1.0, total))

    return {
        "keyword": round(keyword_score, 3),
        "keyword_hits": keyword_hits,
        "engagement": round(engagement_score, 3),
        "engagement_raw": engagement,
        "tech": round(tech_score, 3),
        "tech_hits": tech_hits,
        "gap": round(gap_score, 3),
        "gap_hits": gap_hits,
        "author": round(author_score, 3),
        "recency": round(recency, 3),
        "total": round(total, 3)
    }

print("Scraping posts...")
init_db()
posts = scrape_posts()
print(f"Found {len(posts)} posts\n")

# Score all posts
scored_posts = []
for post in posts:
    breakdown = debug_score(post)
    scored_posts.append((post, breakdown))

# Sort by total score
scored_posts.sort(key=lambda x: x[1]["total"], reverse=True)

# Print top 10
print("=" * 80)
print("TOP 10 POSTS BY SCORE")
print("=" * 80)

for i, (post, breakdown) in enumerate(scored_posts[:10]):
    print(f"\n#{i+1} — Score: {breakdown['total']} — @{post.get('author', 'unknown')}")
    print(f"    Likes: {post.get('like_count', 0)} | Reposts: {post.get('repost_count', 0)}")
    print(f"    Text: {post.get('text', '')[:100]}...")
    print(f"    Breakdown:")
    print(f"      keyword:    {breakdown['keyword']} ({breakdown['keyword_hits']} hits)")
    print(f"      engagement: {breakdown['engagement']} (raw: {breakdown['engagement_raw']})")
    print(f"      tech:       {breakdown['tech']} ({breakdown['tech_hits']} hits)")
    print(f"      gap:        {breakdown['gap']} ({breakdown['gap_hits']} hits)")
    print(f"      author:     {breakdown['author']}")
    print(f"      recency:    {breakdown['recency']}")

print("\n" + "=" * 80)
print(f"Posts >= 0.65: {sum(1 for _, b in scored_posts if b['total'] >= 0.65)}")
print(f"Posts >= 0.50: {sum(1 for _, b in scored_posts if b['total'] >= 0.50)}")
print(f"Posts >= 0.40: {sum(1 for _, b in scored_posts if b['total'] >= 0.40)}")
print("=" * 80)
