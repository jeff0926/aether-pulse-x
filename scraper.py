# scraper.py
# READ-ONLY X scraper via Apify — NO Twitter write API calls
from apify_client import ApifyClient
from config import APIFY_API_TOKEN, APIFY_ACTOR_ID, KEYWORDS


def scrape_posts():
    """
    Run Apify Tweet Scraper V2 for all keywords.
    Returns list of post dicts with text, url, author, engagement.

    NOTE: This is READ-ONLY scraping. No Twitter write operations.
    """
    client = ApifyClient(APIFY_API_TOKEN)
    all_posts = []

    for query in KEYWORDS:
        run_input = {
            "searchTerms": [query],
            "maxItems": 20,
            "sort": "Latest",
            "lang": "en"
        }

        try:
            run = client.actor(APIFY_ACTOR_ID).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

            for item in items:
                post = {
                    "id": item.get("id", ""),
                    "text": item.get("text", ""),
                    "url": item.get("url", ""),
                    "author": item.get("author", {}).get("userName", ""),
                    "like_count": item.get("likeCount", 0),
                    "repost_count": item.get("retweetCount", 0),
                    "reply_count": item.get("replyCount", 0),
                    "view_count": item.get("viewCount", 0),
                    "created_at": item.get("createdAt", "")
                }
                if post["id"]:
                    all_posts.append(post)

        except Exception as e:
            print(f"Scraper error for query '{query}': {e}")
            continue

    # Deduplicate by post ID
    seen = set()
    unique_posts = []
    for post in all_posts:
        if post["id"] not in seen:
            seen.add(post["id"])
            unique_posts.append(post)

    return unique_posts
