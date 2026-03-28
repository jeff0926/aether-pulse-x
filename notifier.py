# notifier.py
# =============================================================================
# TELEGRAM ONLY — NO TWITTER WRITE API
# =============================================================================
# This module ONLY sends drafts to Telegram for human review.
# Jeff copies the draft and posts manually. NEVER auto-post to X.
# There are ZERO Twitter/X write API calls in this entire codebase.
# =============================================================================

import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


async def send_telegram_async(message):
    """Send message to Telegram. This is the ONLY external write operation."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,
        parse_mode="HTML"
    )


def send_draft_to_telegram(post, draft, x_adjusted_length):
    """
    Send a formatted draft to Jeff via Telegram.

    HUMAN-IN-THE-LOOP GUARANTEE:
    - This sends a DRAFT to Telegram
    - Jeff reviews the draft
    - Jeff manually copies and posts to X
    - No auto-posting. Ever.
    """
    hours_old = post.get('hours_old')
    recency_display = f"{hours_old}h ago" if hours_old is not None else "Unknown"
    tier = post.get('tier', '?')
    gap = post.get('gap_identified') or "General relevance"
    reasoning = post.get('reasoning', '')[:100]

    message = f"""<b>AETHER-PULSE-X</b>

<b>Post by @{post['author']}</b>
Tier: {tier} | Score: {post.get('score', 0)} | Likes: {post.get('like_count', 0)}
Posted: {recency_display}

<b>Why this post:</b>
{reasoning}

<b>Gap identified:</b>
{gap}

<b>Original:</b>
{post['text'][:300]}

<b>Post URL:</b>
{post['url']}

<b>Draft Reply (copy and post):</b>
<code>{draft}</code>

<i>Characters: {x_adjusted_length}/280 (X-adjusted)</i>

<b>After posting: Follow @{post['author']}</b>"""

    asyncio.run(send_telegram_async(message))


def send_snapshot_draft_to_telegram(result):
    """
    Send a snapshot-generated draft to Jeff via Telegram.
    Used for --snapshot and --url modes.
    """
    message = f"""<b>AETHER-PULSE-X SNAPSHOT</b>

<b>Claim detected:</b>
{result.get('claim', 'N/A')}

<b>Gap AETHER fills:</b>
{result.get('gap', 'N/A')}

<b>Draft ({result.get('type', 'reply').upper()}) — copy and post:</b>
<code>{result.get('draft', 'N/A')}</code>

<b>Remember to follow the author after posting</b>"""

    asyncio.run(send_telegram_async(message))
