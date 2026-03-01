#!/usr/bin/env python3
"""
GraceBox — Shared Database Module
SQLite database initialization and helper functions used by all API endpoints.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime

# Database file lives in the project root directory
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gracebox.db")

# Fallback: if that path doesn't work in CGI context, use working directory
if not os.path.isdir(os.path.dirname(DB_PATH)):
    DB_PATH = "gracebox.db"


def get_db():
    """Get a database connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT '',
            subscription_tier TEXT DEFAULT 'free' CHECK(subscription_tier IN ('free','personal','professional','team')),
            subscription_status TEXT DEFAULT 'active' CHECK(subscription_status IN ('active','cancelled','past_due','trialing')),
            stripe_customer_id TEXT DEFAULT '',
            max_screened_senders INTEGER DEFAULT 1,
            max_emails_per_month INTEGER DEFAULT 25,
            emails_processed_this_month INTEGER DEFAULT 0,
            sender_notification_enabled INTEGER DEFAULT 1,
            tone_threshold REAL DEFAULT 0.3,
            retention_days INTEGER DEFAULT 90,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS screened_senders (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            sender_email TEXT NOT NULL,
            sender_name TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            notify_sender INTEGER DEFAULT 1,
            emails_screened_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, sender_email)
        );

        CREATE TABLE IF NOT EXISTS email_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            screened_sender_id TEXT,
            original_subject TEXT DEFAULT '',
            original_body TEXT DEFAULT '',
            rewritten_body TEXT DEFAULT '',
            tone_score REAL DEFAULT 0.0,
            tone_reason TEXT DEFAULT '',
            was_rewritten INTEGER DEFAULT 0,
            sender_notified INTEGER DEFAULT 0,
            processed_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (screened_sender_id) REFERENCES screened_senders(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_senders_user ON screened_senders(user_id);
        CREATE INDEX IF NOT EXISTS idx_logs_user ON email_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_logs_sender ON email_logs(screened_sender_id);
    """)
    conn.commit()
    conn.close()


# Tier configuration
TIER_LIMITS = {
    "free":         {"max_screened_senders": 1,  "max_emails_per_month": 25,   "notifications": False},
    "personal":     {"max_screened_senders": 10, "max_emails_per_month": 200,  "notifications": True},
    "professional": {"max_screened_senders": 25, "max_emails_per_month": 500,  "notifications": True},
    "team":         {"max_screened_senders": 50, "max_emails_per_month": 1000, "notifications": True},
}


def new_id():
    """Generate a new UUID."""
    return str(uuid.uuid4())


def row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    """Convert a list of sqlite3.Row to a list of dicts."""
    return [dict(r) for r in rows]


def json_response(data, status=200):
    """Print a JSON response with appropriate CGI headers."""
    if status != 200:
        print(f"Status: {status}")
    print("Content-Type: application/json")
    print()
    print(json.dumps(data, default=str))


def error_response(message, status=400):
    """Print a JSON error response."""
    print(f"Status: {status}")
    print("Content-Type: application/json")
    print()
    print(json.dumps({"error": message}))


def read_body():
    """Read the request body from stdin."""
    import sys
    content_length = int(os.environ.get("CONTENT_LENGTH", 0))
    if content_length > 0:
        return json.loads(sys.stdin.read(content_length))
    return {}


def parse_query():
    """Parse the QUERY_STRING into a dict."""
    from urllib.parse import parse_qs
    qs = os.environ.get("QUERY_STRING", "")
    params = parse_qs(qs)
    # Flatten single-value params
    return {k: v[0] if len(v) == 1 else v for k, v in params.items()}


def validate_email(email):
    """Basic email format validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# Initialize the database on import
init_db()
