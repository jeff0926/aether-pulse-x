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
