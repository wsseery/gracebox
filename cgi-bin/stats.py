#!/usr/bin/env python3
"""
GraceBox — Stats API
Returns dashboard statistics for a user.

GET    ?user_id=X    → Get usage stats and summary data
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import get_db, row_to_dict, json_response, error_response, parse_query

def handle_get(params):
    if "user_id" not in params:
        return error_response("user_id is required")

    user_id = params["user_id"]
    db = get_db()

    # Get user
    user = db.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
    if not user:
        return error_response("User not found", 404)

    # Count active senders
    senders_count = db.execute("""
        SELECT COUNT(*) as cnt FROM screened_senders
        WHERE user_id = ? AND is_active = 1
    """, [user_id]).fetchone()["cnt"]

    total_senders = db.execute("""
        SELECT COUNT(*) as cnt FROM screened_senders
        WHERE user_id = ?
    """, [user_id]).fetchone()["cnt"]

    # Email stats
    total_emails = db.execute("""
        SELECT COUNT(*) as cnt FROM email_logs WHERE user_id = ?
    """, [user_id]).fetchone()["cnt"]

    rewritten_count = db.execute("""
        SELECT COUNT(*) as cnt FROM email_logs
        WHERE user_id = ? AND was_rewritten = 1
    """, [user_id]).fetchone()["cnt"]

    avg_tone = db.execute("""
        SELECT COALESCE(AVG(tone_score), 0.0) as avg_score FROM email_logs
        WHERE user_id = ? AND tone_score > 0
    """, [user_id]).fetchone()["avg_score"]

    # Recent activity (last 7 days)
    recent_count = db.execute("""
        SELECT COUNT(*) as cnt FROM email_logs
        WHERE user_id = ? AND processed_at >= datetime('now', '-7 days')
    """, [user_id]).fetchone()["cnt"]

    recent_rewritten = db.execute("""
        SELECT COUNT(*) as cnt FROM email_logs
        WHERE user_id = ? AND was_rewritten = 1 AND processed_at >= datetime('now', '-7 days')
    """, [user_id]).fetchone()["cnt"]

    # Top senders by volume
    top_senders = db.execute("""
        SELECT ss.sender_email, ss.sender_name, ss.emails_screened_count
        FROM screened_senders ss
        WHERE ss.user_id = ?
        ORDER BY ss.emails_screened_count DESC
        LIMIT 5
    """, [user_id]).fetchall()

    return json_response({
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "subscription_tier": user["subscription_tier"],
            "subscription_status": user["subscription_status"],
            "tone_threshold": user["tone_threshold"],
        },
        "usage": {
            "senders_active": senders_count,
            "senders_total": total_senders,
            "senders_limit": user["max_screened_senders"],
            "senders_pct": round((senders_count / max(user["max_screened_senders"], 1)) * 100, 1),
            "emails_processed_this_month": user["emails_processed_this_month"],
            "emails_limit": user["max_emails_per_month"],
            "emails_pct": round((user["emails_processed_this_month"] / max(user["max_emails_per_month"], 1)) * 100, 1),
        },
        "stats": {
            "total_emails_processed": total_emails,
            "total_rewritten": rewritten_count,
            "rewrite_rate_pct": round((rewritten_count / max(total_emails, 1)) * 100, 1),
            "avg_tone_score": round(avg_tone, 3),
            "last_7_days_processed": recent_count,
            "last_7_days_rewritten": recent_rewritten,
        },
        "top_senders": [dict(r) for r in top_senders],
    })


def main():
    method = os.environ.get("REQUEST_METHOD", "GET")
    params = parse_query()

    try:
        if method == "GET":
            handle_get(params)
        else:
            error_response(f"Method {method} not allowed", 405)
    except Exception as e:
        error_response(f"Internal error: {str(e)}", 500)


if __name__ == "__main__":
    main()
