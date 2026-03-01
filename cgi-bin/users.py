#!/usr/bin/env python3
"""
GraceBox — Users API
Handles user account creation, retrieval, and settings updates.

GET    ?id=X           → Get user profile
GET    ?email=X        → Get user by email
POST                   → Create new user { email, name }
PATCH  ?id=X           → Update settings { sender_notification_enabled, tone_threshold, retention_days, subscription_tier }
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import (get_db, init_db, new_id, row_to_dict, json_response,
                error_response, read_body, parse_query, validate_email, TIER_LIMITS)

def handle_get(params):
    db = get_db()
    if "id" in params:
        row = db.execute("SELECT * FROM users WHERE id = ?", [params["id"]]).fetchone()
        if not row:
            return error_response("User not found", 404)
        return json_response(row_to_dict(row))
    elif "email" in params:
        row = db.execute("SELECT * FROM users WHERE email = ?", [params["email"]]).fetchone()
        if not row:
            return error_response("User not found", 404)
        return json_response(row_to_dict(row))
    else:
        # List all users (admin/debug — limit to 100)
        rows = db.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 100").fetchall()
        return json_response([row_to_dict(r) for r in rows])


def handle_post():
    body = read_body()
    email = body.get("email", "").strip().lower()
    name = body.get("name", "").strip()

    if not email:
        return error_response("Email is required")
    if not validate_email(email):
        return error_response("Invalid email format")

    db = get_db()

    # Check if user already exists
    existing = db.execute("SELECT * FROM users WHERE email = ?", [email]).fetchone()
    if existing:
        return json_response(row_to_dict(existing))

    user_id = new_id()
    tier = "free"
    limits = TIER_LIMITS[tier]

    db.execute("""
        INSERT INTO users (id, email, name, subscription_tier, max_screened_senders, max_emails_per_month)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [user_id, email, name, tier, limits["max_screened_senders"], limits["max_emails_per_month"]])
    db.commit()

    row = db.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
    print("Status: 201")
    print("Content-Type: application/json")
    print()
    import json
    print(json.dumps(row_to_dict(row), default=str))
    return


def handle_patch(params):
    if "id" not in params:
        return error_response("User ID is required")

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", [params["id"]]).fetchone()
    if not user:
        return error_response("User not found", 404)

    body = read_body()
    updates = []
    values = []

    # Allowed fields to update
    allowed_fields = {
        "name": str,
        "sender_notification_enabled": int,
        "tone_threshold": float,
        "retention_days": int,
        "subscription_tier": str,
        "subscription_status": str,
        "stripe_customer_id": str,
        "emails_processed_this_month": int,
    }

    for field, field_type in allowed_fields.items():
        if field in body:
            val = body[field]
            # Special handling for subscription_tier — update limits too
            if field == "subscription_tier":
                if val not in TIER_LIMITS:
                    return error_response(f"Invalid tier: {val}. Must be one of: {', '.join(TIER_LIMITS.keys())}")
                limits = TIER_LIMITS[val]
                updates.append("max_screened_senders = ?")
                values.append(limits["max_screened_senders"])
                updates.append("max_emails_per_month = ?")
                values.append(limits["max_emails_per_month"])

            if field == "tone_threshold":
                val = max(0.1, min(0.9, float(val)))

            updates.append(f"{field} = ?")
            values.append(val)

    if not updates:
        return error_response("No valid fields to update")

    updates.append("updated_at = datetime('now')")
    values.append(params["id"])

    db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
    db.commit()

    row = db.execute("SELECT * FROM users WHERE id = ?", [params["id"]]).fetchone()
    return json_response(row_to_dict(row))


def main():
    method = os.environ.get("REQUEST_METHOD", "GET")
    params = parse_query()

    try:
        if method == "GET":
            handle_get(params)
        elif method == "POST":
            handle_post()
        elif method == "PATCH":
            handle_patch(params)
        else:
            error_response(f"Method {method} not allowed", 405)
    except Exception as e:
        error_response(f"Internal error: {str(e)}", 500)


if __name__ == "__main__":
    main()
