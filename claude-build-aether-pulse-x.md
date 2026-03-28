# aether-pulse-x — Build Specification
**Version:** 1.0
**Date:** 2026-03-26
**Builder:** Claude Code
**Owner:** 864 Zeros LLC

---

## Build Overview

Build aether-pulse-x — a Python feature brick that:
1. Scrapes X for high-engagement AI agent posts via Apify
2. Scores each post for relevance to AETHER
3. Drafts a kind, technical reply in Jeff Conn's voice via Claude API
4. Delivers the draft to Jeff via Telegram
5. Logs engagement results for self-education

One human action: Jeff copies the draft from Telegram and posts it.
Auto-posting is never implemented. Ever.

---

## Input → Process → Output

```
INPUT:
  - Apify API token
  - Anthropic API key
  - Telegram bot token + chat ID
  - Keyword config (8 search queries)
  - Score threshold (0.65)
  - Max drafts per day (3)

PROCESS:
  1. Run Apify Tweet Scraper V2 for each keyword
  2. Deduplicate results (remove already-replied posts)
  3. Score each post 0.0-1.0 for relevance
  4. Filter posts above threshold (0.65)
  5. Rank by score, take top N (up to max drafts per day)
  6. Generate reply draft via Claude API
  7. Send draft to Jeff via Telegram
  8. Log all activity to SQLite

OUTPUT:
  - Telegram message per qualifying post containing:
    - Original post text
    - Original post URL
    - Author handle
    - Post score
    - Ready-to-post reply draft
  - SQLite engagement log entry
  - DAI Pulse JSON broadcast (for dashboard)
```

---

## Step 1 — Project Setup

```bash
mkdir aether-pulse-x
cd aether-pulse-x
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install apify-client anthropic python-telegram-bot python-dotenv
```

Create `.env`:
```
APIFY_API_TOKEN=your_token_here
ANTHROPIC_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
ZENODO_URL=https://zenodo.org/records/19212829
GITHUB_URL=https://github.com/jeff0926/aether
SCORE_THRESHOLD=0.65
MAX_DRAFTS_PER_DAY=3
RUN_INTERVAL_HOURS=6
```

---

## Step 2 — config.py

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ZENODO_URL = os.getenv("ZENODO_URL", "https://zenodo.org/records/19212829")
GITHUB_URL = os.getenv("GITHUB_URL", "https://github.com/jeff0926/aether")
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.65"))
MAX_DRAFTS_PER_DAY = int(os.getenv("MAX_DRAFTS_PER_DAY", "3"))
RUN_INTERVAL_HOURS = int(os.getenv("RUN_INTERVAL_HOURS", "6"))

# Apify actor ID for Tweet Scraper V2
APIFY_ACTOR_ID = "61RPP7dywgiy0JPD0"

# Keywords to monitor
KEYWORDS = [
    '"AI agents" min_faves:50 lang:en -filter:retweets',
    '"agentic AI" min_faves:50 lang:en -filter:retweets',
    '".claude/agents" min_faves:50 lang:en',
    '"SKILL.md" min_faves:50 lang:en',
    '"agent framework" min_faves:50 lang:en -filter:retweets',
    '"LLM verification" min_faves:50 lang:en',
    '"agent harness" min_faves:50 lang:en',
    '"building agents" min_faves:50 lang:en -filter:retweets',
    '"microservice" "agents" min_faves:50 lang:en',
    '"prompt wrapper" min_faves:50 lang:en'
]

# Proof points for reply drafts — verified facts only
PROOF_POINTS = {
    "score_improvement": "0.143 → 0.889",
    "human_intervention": "zero human intervention",
    "verification_speed": "sub-millisecond verification",
    "tech_stack": "no embeddings, no vector DB",
    "tagline": "The model didn't change. The skill did.",
    "thesis": "Intelligence is intrinsic to the system, not the model.",
    "zenodo": ZENODO_URL
}

# Gap signals — phrases that indicate missing verification/education
GAP_SIGNALS = [
    "flat markdown",
    "prompt wrapper",
    "tool router",
    "microservice",
    "agent harness",
    "chaining",
    "orchestrat",
    "no memory",
    "stateless",
    "fails",
    "hallucinate",
    "unreliable"
]

# Technical depth signals
TECH_SIGNALS = [
    "architecture",
    "framework",
    "pipeline",
    "knowledge graph",
    "verification",
    "grounding",
    "self-educat",
    "self-heal",
    "capsule",
    "agent",
    "skill",
    "LLM",
    "reasoning"
]
```

---

## Step 3 — logger.py

Build this first. Everything else logs to it.

```python
# logger.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/engagement_log.db")
REPLIED_PATH = Path("data/replied_posts.json")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            url TEXT,
            author TEXT,
            text TEXT,
            score REAL,
            draft TEXT,
            telegram_sent INTEGER DEFAULT 0,
            jeff_posted INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            link_clicks INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at TEXT,
            posts_found INTEGER,
            posts_scored INTEGER,
            posts_qualified INTEGER,
            drafts_sent INTEGER
        )
    """)
    conn.commit()
    conn.close()

def load_replied_posts():
    if REPLIED_PATH.exists():
        return set(json.loads(REPLIED_PATH.read_text()))
    return set()

def save_replied_post(post_id):
    replied = load_replied_posts()
    replied.add(post_id)
    REPLIED_PATH.parent.mkdir(exist_ok=True)
    REPLIED_PATH.write_text(json.dumps(list(replied)))

def log_post(post_id, url, author, text, score, draft):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO posts 
        (id, url, author, text, score, draft, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (post_id, url, author, text, score, draft,
          datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def log_telegram_sent(post_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE posts SET telegram_sent=1, updated_at=? WHERE id=?",
        (datetime.now().isoformat(), post_id)
    )
    conn.commit()
    conn.close()

def log_run(posts_found, posts_scored, posts_qualified, drafts_sent):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO runs (run_at, posts_found, posts_scored, posts_qualified, drafts_sent)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), posts_found, posts_scored,
          posts_qualified, drafts_sent))
    conn.commit()
    conn.close()

def get_drafts_sent_today():
    conn = sqlite3.connect(DB_PATH)
    today = datetime.now().date().isoformat()
    result = conn.execute("""
        SELECT COUNT(*) FROM posts 
        WHERE telegram_sent=1 AND date(created_at)=?
    """, (today,)).fetchone()
    conn.close()
    return result[0] if result else 0
```

---

## Step 4 — scraper.py

```python
# scraper.py
from apify_client import ApifyClient
from config import APIFY_API_TOKEN, APIFY_ACTOR_ID, KEYWORDS

def scrape_posts():
    """
    Run Apify Tweet Scraper V2 for all keywords.
    Returns list of post dicts with text, url, author, engagement.
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
```

---

## Step 5 — scorer.py

```python
# scorer.py
from config import GAP_SIGNALS, TECH_SIGNALS, SCORE_THRESHOLD

def score_post(post):
    """
    Score a post 0.0-1.0 for relevance to AETHER.
    Returns score float.
    """
    text = post["text"].lower()
    score = 0.0

    # Keyword match signal (0.30)
    keyword_hits = sum(1 for kw in TECH_SIGNALS if kw.lower() in text)
    score += min(keyword_hits / len(TECH_SIGNALS), 1.0) * 0.30

    # Engagement signal (0.25)
    likes = post.get("like_count", 0)
    reposts = post.get("repost_count", 0)
    replies = post.get("reply_count", 0)
    engagement = likes + (reposts * 2) + replies
    # Normalize: 50 engagement = 0.25, 500+ = full 0.25
    engagement_score = min(engagement / 500, 1.0)
    score += engagement_score * 0.25

    # Technical depth signal (0.20)
    tech_hits = sum(1 for sig in TECH_SIGNALS if sig.lower() in text)
    score += min(tech_hits / 5, 1.0) * 0.20

    # Gap signal (0.15) — does the post reveal what's missing?
    gap_hits = sum(1 for sig in GAP_SIGNALS if sig.lower() in text)
    score += min(gap_hits / 3, 1.0) * 0.15

    # Author relevance (0.10) — basic heuristic
    # If author has "AI", "agent", "ML", "engineer", "researcher" in handle or bio
    author = post.get("author", "").lower()
    relevance_signals = ["ai", "agent", "ml", "engineer", "researcher", "dev", "build"]
    author_hits = sum(1 for sig in relevance_signals if sig in author)
    score += min(author_hits / 2, 1.0) * 0.10

    return round(score, 3)

def filter_qualifying_posts(posts, replied_posts, max_drafts):
    """
    Filter posts above threshold, not already replied to,
    sorted by score descending, limited to max_drafts.
    """
    scored = []
    for post in posts:
        if post["id"] in replied_posts:
            continue
        score = score_post(post)
        if score >= SCORE_THRESHOLD:
            post["score"] = score
            scored.append(post)

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Return top N
    return scored[:max_drafts]
```

---

## Step 6 — drafter.py

```python
# drafter.py
import anthropic
from config import ANTHROPIC_API_KEY, PROOF_POINTS, ZENODO_URL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are drafting a reply to an X (Twitter) post on behalf of Jeff Conn, 
founder of 864 Zeros LLC and creator of AETHER — a self-verifying, self-educating agent framework.

Jeff's voice is: direct, technical, kind, curious. Never promotional. Never aggressive.
He engages as a peer, not a marketer.

AETHER key facts (use only these — never fabricate):
- Any .md file becomes a self-verifying, self-educating agent capsule
- Jefferson capsule: AEC score 0.143 → 0.889, zero human intervention
- Sub-millisecond verification. No embeddings. No vector DB.
- Intelligence is intrinsic to the system, not the model
- The model didn't change. The skill did.
- Paper: {zenodo_url}

Reply rules:
1. Maximum 280 characters total including the URL
2. Start with one kind acknowledgment of what's interesting or valid
3. Identify the specific gap AETHER addresses — one sentence
4. One sentence on what AETHER does or proves
5. End with the Zenodo URL
6. No hashtags. No emojis. No exclamation points.
7. Never mention SAP or any employer
8. Never claim more than what the facts above support
""".format(zenodo_url=ZENODO_URL)

def draft_reply(post):
    """
    Generate a reply draft for a qualifying post.
    Returns draft string under 280 characters.
    """
    user_prompt = f"""Post by @{post['author']}:
"{post['text']}"

Post URL: {post['url']}
Likes: {post.get('like_count', 0)}
Score: {post.get('score', 0)}

Draft a reply that:
1. Acknowledges what's technically interesting about their approach
2. Identifies the specific verification or self-education gap
3. States what AETHER does about it
4. Ends with the paper URL

Keep it under 280 characters total. Be kind and technical."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    draft = message.content[0].text.strip()

    # Enforce character limit
    if len(draft) > 280:
        # Truncate and ensure URL is present
        draft = draft[:250] + f"\n{ZENODO_URL}"

    return draft
```

---

## Step 7 — notifier.py

```python
# notifier.py
import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

async def send_telegram_async(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,
        parse_mode="HTML"
    )

def send_draft_to_telegram(post, draft):
    """
    Send a formatted draft to Jeff via Telegram.
    """
    message = f"""🎯 <b>AETHER-PULSE-X</b>

<b>Post by @{post['author']}</b>
Score: {post.get('score', 0)} | Likes: {post.get('like_count', 0)}

<b>Original:</b>
{post['text'][:300]}

<b>Post URL:</b>
{post['url']}

<b>Draft Reply (copy and post):</b>
<code>{draft}</code>

<i>Characters: {len(draft)}/280</i>"""

    asyncio.run(send_telegram_async(message))
```

---

## Step 8 — pulse_x.py (Main Entry Point)

```python
# pulse_x.py
import json
from datetime import datetime
from config import MAX_DRAFTS_PER_DAY, SCORE_THRESHOLD
from scraper import scrape_posts
from scorer import filter_qualifying_posts
from drafter import draft_reply
from notifier import send_draft_to_telegram
from logger import (
    init_db, load_replied_posts, save_replied_post,
    log_post, log_telegram_sent, log_run, get_drafts_sent_today
)

def run():
    print(f"[{datetime.now().isoformat()}] aether-pulse-x starting...")

    # Initialize database
    init_db()

    # Check daily draft limit
    drafts_today = get_drafts_sent_today()
    remaining = MAX_DRAFTS_PER_DAY - drafts_today
    if remaining <= 0:
        print(f"Daily draft limit reached ({MAX_DRAFTS_PER_DAY}). Exiting.")
        return

    # Load already-replied posts
    replied_posts = load_replied_posts()

    # Scrape X for qualifying posts
    print("Scraping X via Apify...")
    posts = scrape_posts()
    print(f"Found {len(posts)} posts")

    # Score and filter
    qualifying = filter_qualifying_posts(posts, replied_posts, remaining)
    print(f"Qualifying posts (score >= {SCORE_THRESHOLD}): {len(qualifying)}")

    # Draft and notify
    drafts_sent = 0
    for post in qualifying:
        try:
            print(f"Drafting reply for @{post['author']} (score: {post['score']})")
            draft = draft_reply(post)

            # Send to Telegram
            send_draft_to_telegram(post, draft)

            # Log everything
            log_post(post["id"], post["url"], post["author"],
                    post["text"], post["score"], draft)
            log_telegram_sent(post["id"])
            save_replied_post(post["id"])

            drafts_sent += 1
            print(f"Draft sent to Telegram for post {post['id']}")

        except Exception as e:
            print(f"Error processing post {post['id']}: {e}")
            continue

    # Log the run
    log_run(len(posts), len(qualifying), len(qualifying), drafts_sent)

    # Broadcast DAI Pulse
    dai_pulse = {
        "phase": "complete",
        "source": "aether-pulse-x",
        "timestamp": datetime.now().isoformat(),
        "content": {
            "posts_found": str(len(posts)),
            "posts_qualified": str(len(qualifying)),
            "drafts_sent": str(drafts_sent),
            "daily_total": str(drafts_today + drafts_sent)
        }
    }
    print(f"DAI Pulse: {json.dumps(dai_pulse, indent=2)}")
    print(f"[{datetime.now().isoformat()}] aether-pulse-x complete. Drafts sent: {drafts_sent}")

if __name__ == "__main__":
    run()
```

---

## Step 9 — AETHER Capsule Files

### capsule/manifest.json
```json
{
  "id": "aether-pulse-x-v1.0.0",
  "name": "AETHER Pulse X",
  "version": "1.0.0",
  "type": "gtm-agent",
  "department": "GTM Office",
  "created": "2026-03-26",
  "parent": "aether-pulse",
  "platform": "x-twitter"
}
```

### capsule/definition.json
```json
{
  "pipeline": {
    "distill": {"enabled": true},
    "augment": {"enabled": true},
    "generate": {"enabled": true},
    "review": {"enabled": true}
  },
  "review": {
    "threshold": 0.80
  },
  "domain": "social-engagement",
  "platform": "x-twitter",
  "output": "telegram-draft",
  "auto_post": false,
  "max_drafts_per_day": 3
}
```

### capsule/persona.json
```json
{
  "name": "SIGNAL — Social Engagement Agent",
  "voice": "Jeff Conn",
  "tone": "direct, technical, kind, curious",
  "constraints": [
    "never promotional",
    "never aggressive",
    "never auto-post",
    "never fabricate metrics",
    "never mention employer",
    "maximum 280 characters per reply"
  ],
  "proof_points": [
    "AEC score 0.143 → 0.889, zero human intervention",
    "Sub-millisecond verification, no embeddings, no vector DB",
    "The model didn't change. The skill did."
  ]
}
```

### capsule/kb.md
```markdown
# AETHER Pulse X — Knowledge Base

## What AETHER Is
AETHER is a self-verifying, self-educating agent framework. Every agent is a 5-file
capsule with its own typed knowledge graph that compiles into deterministic verification
logic at load time. When verification fails, the agent self-educates — researches the gap,
validates new knowledge, and integrates it. The model is replaceable. The skill is the asset.

## Proven Engagement Pattern (2026-03-26)
Reply to @Suryanshti777 showing .claude/agents/ flat markdown files.
Result: 735 impressions, 200 engagements, 131 link clicks, 18% CTR.
Pattern: Kind acknowledgment + specific gap + what we built + Zenodo link.

## Verified Proof Points
- Jefferson capsule: AEC score 0.143 → 0.889
- 17 knowledge triples acquired autonomously
- Zero human intervention during education cycle
- Sub-millisecond verification
- No embeddings, no vector DB, no GPU
- frontend-design SKILL.md → 73-node verification engine in one pass

## The Gap AETHER Addresses
Most agent systems today are flat markdown files, prompt wrappers, or microservice
orchestrators. They have no verification layer. They have no self-education loop.
They fail the same way every time. AETHER adds the missing layer.

## Paper
DOI: 10.5281/zenodo.19212829
URL: https://zenodo.org/records/19212829
Repo: https://github.com/jeff0926/aether
```

---

## Step 10 — Tests

### tests/test_scorer.py
```python
def test_high_relevance_post():
    post = {
        "id": "test1",
        "text": "Building AI agents with flat markdown files as agent definitions",
        "author": "aibuilder",
        "like_count": 150,
        "repost_count": 30,
        "reply_count": 10,
        "view_count": 5000
    }
    score = score_post(post)
    assert score >= 0.65, f"Expected score >= 0.65, got {score}"

def test_low_relevance_post():
    post = {
        "id": "test2",
        "text": "Great weather today in San Francisco",
        "author": "randomuser",
        "like_count": 5,
        "repost_count": 0,
        "reply_count": 1,
        "view_count": 100
    }
    score = score_post(post)
    assert score < 0.65, f"Expected score < 0.65, got {score}"

def test_deduplication():
    replied = {"post123"}
    posts = [
        {"id": "post123", "text": "AI agents framework", "like_count": 100,
         "repost_count": 20, "reply_count": 5, "view_count": 2000, "author": "dev"},
        {"id": "post456", "text": "agent harness architecture", "like_count": 200,
         "repost_count": 50, "reply_count": 15, "view_count": 5000, "author": "mleng"}
    ]
    qualifying = filter_qualifying_posts(posts, replied, 3)
    assert not any(p["id"] == "post123" for p in qualifying)
```

---

## Step 11 — Scheduling

Run every 6 hours via cron or Apify scheduled task:

```bash
# crontab entry
0 */6 * * * cd /path/to/aether-pulse-x && python pulse_x.py >> logs/pulse.log 2>&1
```

Or run once manually:
```bash
python pulse_x.py
```

---

## Done Criteria

Claude Code build is complete when:

- [ ] All 8 Python files created and functional
- [ ] AETHER capsule directory with all 5 files
- [ ] `.env.example` created with all required variables
- [ ] `tests/` directory with passing scorer tests
- [ ] `data/` directory initialized with empty SQLite DB
- [ ] Single `python pulse_x.py` run completes without errors
- [ ] Telegram message delivered with properly formatted draft
- [ ] Replied posts deduplication working
- [ ] Daily limit enforced
- [ ] DAI Pulse JSON printed to stdout on completion

---

## Never Do

- **NEVER implement auto-posting to X** — Telegram draft only
- **NEVER fabricate engagement metrics** — log only real data
- **NEVER skip the 0.65 score threshold** — quality gate is non-negotiable
- **NEVER reply to same post twice** — deduplication is mandatory
- **NEVER include SAP or employer references** in any draft
- **NEVER add frameworks** — stdlib + apify-client + anthropic + python-telegram-bot only
- **NEVER exceed 280 characters** in a draft reply
- **NEVER send more than 3 drafts per day** — enforce MAX_DRAFTS_PER_DAY
