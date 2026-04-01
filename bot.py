# bot.py
# =============================================================================
# Telegram Bot for aether-pulse-x — runs on Railway
# =============================================================================
# Commands:
#   /scan     - Run discovery now
#   /status   - Show last run stats
#   /url <x>  - Analyze a specific X post URL
# =============================================================================

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MAX_DRAFTS_PER_DAY
from scraper import scrape_posts
from scorer import filter_qualifying_posts
from drafter import draft_reply
from notifier import send_draft_to_telegram
from logger import init_db, load_replied_posts, log_telegram_sent
from snapshot import process_url

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Track last run stats
last_run_stats = {
    "timestamp": None,
    "posts_found": 0,
    "posts_qualified": 0,
    "drafts_sent": 0
}


def is_authorized(update: Update) -> bool:
    """Only respond to the authorized chat."""
    return str(update.effective_chat.id) == str(TELEGRAM_CHAT_ID)


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run the discovery flow."""
    if not is_authorized(update):
        return

    await update.message.reply_text("Scanning for posts...")

    try:
        # Initialize
        init_db()
        replied_posts = load_replied_posts()

        # Scrape
        posts = scrape_posts()
        if not posts:
            await update.message.reply_text("No posts found from scraper.")
            return

        await update.message.reply_text(f"Found {len(posts)} posts. Scoring...")

        # Score and filter
        qualifying = filter_qualifying_posts(posts, replied_posts, MAX_DRAFTS_PER_DAY)

        if not qualifying:
            await update.message.reply_text(
                f"Scored {len(posts)} posts. None qualified (threshold: 0.65)."
            )
            last_run_stats.update({
                "timestamp": datetime.now().isoformat(),
                "posts_found": len(posts),
                "posts_qualified": 0,
                "drafts_sent": 0
            })
            return

        await update.message.reply_text(
            f"{len(qualifying)} posts qualified. Drafting replies..."
        )

        # Draft and send
        drafts_sent = 0
        for post in qualifying:
            draft, x_len = draft_reply(post)
            if draft:
                await send_draft_to_telegram(post, draft, x_len)
                log_telegram_sent(post["id"])
                drafts_sent += 1

        # Update stats
        last_run_stats.update({
            "timestamp": datetime.now().isoformat(),
            "posts_found": len(posts),
            "posts_qualified": len(qualifying),
            "drafts_sent": drafts_sent
        })

        await update.message.reply_text(f"Done. Sent {drafts_sent} drafts.")

    except Exception as e:
        logger.error(f"Scan error: {e}")
        await update.message.reply_text(f"Error: {str(e)[:200]}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show last run stats."""
    if not is_authorized(update):
        return

    if not last_run_stats["timestamp"]:
        await update.message.reply_text("No runs yet since bot started.")
        return

    msg = f"""Last run: {last_run_stats['timestamp']}
Posts found: {last_run_stats['posts_found']}
Posts qualified: {last_run_stats['posts_qualified']}
Drafts sent: {last_run_stats['drafts_sent']}"""

    await update.message.reply_text(msg)


async def url_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze a specific X post URL."""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /url <x_post_url>")
        return

    url = context.args[0]
    await update.message.reply_text(f"Analyzing {url}...")

    try:
        result = process_url(url)
        if result:
            from notifier import send_snapshot_draft_to_telegram
            await send_snapshot_draft_to_telegram(result)
            await update.message.reply_text("Draft sent.")
        else:
            await update.message.reply_text("Could not analyze URL.")
    except Exception as e:
        logger.error(f"URL analysis error: {e}")
        await update.message.reply_text(f"Error: {str(e)[:200]}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available commands."""
    if not is_authorized(update):
        return

    msg = """AETHER-PULSE-X Bot

/scan - Run discovery now
/status - Show last run stats
/url <link> - Analyze specific X post
/help - Show this message"""

    await update.message.reply_text(msg)


def main():
    """Start the bot."""
    print("Starting aether-pulse-x bot...")
    init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("url", url_command))
    app.add_handler(CommandHandler("help", help_command))

    # Run
    print("Bot is running. Listening for commands...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Bot shutdown: {e}")
