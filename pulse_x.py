# pulse_x.py
# =============================================================================
# aether-pulse-x — Main Entry Point (V1.1)
# =============================================================================
# Three modes:
#   python pulse_x.py                    # Monitor mode (scrape X, score, draft)
#   python pulse_x.py --snapshot img.png # Snapshot mode (analyze image)
#   python pulse_x.py --url https://...  # URL mode (analyze web content)
#
# NEVER auto-posts. Jeff posts manually. Human-in-the-loop always.
# =============================================================================

import sys
import json
from datetime import datetime
from config import MAX_DRAFTS_PER_DAY, SCORE_THRESHOLD
from scraper import scrape_posts
from scorer import filter_qualifying_posts
from drafter import draft_reply
from notifier import send_draft_to_telegram, send_snapshot_draft_to_telegram
from logger import (
    init_db, load_replied_posts, save_replied_post,
    log_post, log_telegram_sent, log_run, get_drafts_sent_today
)


def run_monitor_mode():
    """
    Monitor mode: Scrape X for AI agent posts, score, draft replies.
    This is the original v1.0 behavior.
    """
    print(f"[{datetime.now().isoformat()}] aether-pulse-x MONITOR mode starting...")

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

    # Scrape X for qualifying posts (READ-ONLY)
    print("Scraping X via Apify...")
    posts = scrape_posts()
    print(f"Found {len(posts)} posts")

    # Score and filter
    qualifying = filter_qualifying_posts(posts, replied_posts, remaining)
    print(f"Qualifying posts (score >= {SCORE_THRESHOLD}): {len(qualifying)}")

    # Draft and notify (Telegram ONLY — no X posting)
    drafts_sent = 0
    for post in qualifying:
        try:
            print(f"Drafting reply for @{post['author']} (score: {post['score']})")
            draft, x_adjusted_length = draft_reply(post)

            # Send to Telegram (Jeff posts manually)
            send_draft_to_telegram(post, draft, x_adjusted_length)

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
        "mode": "monitor",
        "timestamp": datetime.now().isoformat(),
        "content": {
            "posts_found": str(len(posts)),
            "posts_qualified": str(len(qualifying)),
            "drafts_sent": str(drafts_sent),
            "daily_total": str(drafts_today + drafts_sent)
        }
    }
    print(f"DAI Pulse: {json.dumps(dai_pulse, indent=2)}")
    print(f"[{datetime.now().isoformat()}] aether-pulse-x MONITOR complete. Drafts sent: {drafts_sent}")


def run_snapshot_mode(image_path):
    """
    Snapshot mode: Analyze a screenshot and generate a draft.
    """
    from snapshot import process_snapshot

    print(f"[{datetime.now().isoformat()}] aether-pulse-x SNAPSHOT mode starting...")
    print(f"Processing image: {image_path}")

    result = process_snapshot(image_path)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"Claim: {result.get('claim', 'N/A')}")
    print(f"Gap: {result.get('gap', 'N/A')}")
    print(f"Draft: {result.get('draft', 'N/A')}")
    print(f"Type: {result.get('type', 'N/A')}")

    # Send to Telegram
    send_snapshot_draft_to_telegram(result)

    # Broadcast DAI Pulse
    dai_pulse = {
        "phase": "complete",
        "source": "aether-pulse-x",
        "mode": "snapshot",
        "timestamp": datetime.now().isoformat(),
        "content": {
            "input": image_path,
            "claim": result.get('claim', ''),
            "type": result.get('type', '')
        }
    }
    print(f"DAI Pulse: {json.dumps(dai_pulse, indent=2)}")
    print(f"[{datetime.now().isoformat()}] aether-pulse-x SNAPSHOT complete.")


def run_url_mode(url):
    """
    URL mode: Fetch and analyze a URL, then generate a draft.
    """
    from snapshot import process_url

    print(f"[{datetime.now().isoformat()}] aether-pulse-x URL mode starting...")
    print(f"Processing URL: {url}")

    result = process_url(url)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"Claim: {result.get('claim', 'N/A')}")
    print(f"Gap: {result.get('gap', 'N/A')}")
    print(f"Draft: {result.get('draft', 'N/A')}")
    print(f"Type: {result.get('type', 'N/A')}")

    # Send to Telegram
    send_snapshot_draft_to_telegram(result)

    # Broadcast DAI Pulse
    dai_pulse = {
        "phase": "complete",
        "source": "aether-pulse-x",
        "mode": "url",
        "timestamp": datetime.now().isoformat(),
        "content": {
            "input": url,
            "claim": result.get('claim', ''),
            "type": result.get('type', '')
        }
    }
    print(f"DAI Pulse: {json.dumps(dai_pulse, indent=2)}")
    print(f"[{datetime.now().isoformat()}] aether-pulse-x URL complete.")


def print_usage():
    print("""
aether-pulse-x v1.1 — Social Engagement Monitor & Draft Engine

Usage:
  python pulse_x.py                     Monitor mode (scrape X, score, draft)
  python pulse_x.py --snapshot <image>  Snapshot mode (analyze image)
  python pulse_x.py --url <url>         URL mode (analyze web content)

Examples:
  python pulse_x.py
  python pulse_x.py --snapshot paper_screenshot.png
  python pulse_x.py --url https://arxiv.org/abs/2603.20639
""")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments — run monitor mode
        run_monitor_mode()
    elif sys.argv[1] == '--snapshot':
        if len(sys.argv) < 3:
            print("Error: --snapshot requires an image path")
            print_usage()
            sys.exit(1)
        run_snapshot_mode(sys.argv[2])
    elif sys.argv[1] == '--url':
        if len(sys.argv) < 3:
            print("Error: --url requires a URL")
            print_usage()
            sys.exit(1)
        run_url_mode(sys.argv[2])
    elif sys.argv[1] in ['--help', '-h']:
        print_usage()
    else:
        print(f"Unknown argument: {sys.argv[1]}")
        print_usage()
        sys.exit(1)
