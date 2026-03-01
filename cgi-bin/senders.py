#!/usr/bin/env python3
"""
GraceBox — Screened Senders API
Handles CRUD operations for the email addresses each user wants screened.

GET    ?user_id=X      → List all senders for a user
POST                   → Add sender { user_id, sender_email, sender_name?, notify_sender? }
PATCH  ?id=X           → Update sender { is_active?, notify_sender?, sender_name? }
DELETE ?id=X           → Remove sender
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import (get_db, new_id, row_to_dict, rows_to_list, json_response,
                error_response, read_body, parse_query, validate_email)

def handle_get(params):
    if "user_id" not in params:
        return error_response("user_id is required")

    db = get_db()

    # Verify user exists
    user = db.execute("SELECT * FROM users WHERE id = ?", [params["user_id"]]).fetchone()
    if not user:
        return error_response("User not found", 404)

    rows = db.execute("""
        SELECT * FROM screened_senders
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, [params["user_id"]]).fetchall()

    return json_response(rows_to_list(rows))


def handle_post():
    body = read_body()
    user_id = body.get("user_id", "").strip()
    sender_email = body.get("sender_email", "").strip().lower()
    sender_name = body.get("sender_name", "").strip()
    notify_sender = body.get("notify_sender", 1)

    # Validate required fields
    if not user_id:
        return error_response("user_id is required")
    if not sender_email:
        return error_response("sender_email is required")
    if not validate_email(sender_email):
        return error_response("Invalid sender email format")

    db = get_db()

    # Check user exists
    user = db.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
    if not user:
        return error_response("User not found", 404)

    # Check for duplicate
    existing = db.execute("""
        SELECT * FROM screened_senders
        WHERE user_id = ? AND sender_email = ?
    """, [user_id, sender_email]).fetchone()
    if existing:
        return error_response(f"Sender {sender_email} is already on your screened list")

    # Check tier limit
    current_count = db.execute("""
        SELECT COUNT(*) as cnt FROM screened_senders
        WHERE user_id = ? AND is_active = 1
    """, [user_id]).fetchone()["cnt"]

    if current_count >= user["max_screened_senders"]:
        return error_response(
            f"Sender limit reached ({user['max_screened_senders']} for {user['subscription_tier']} tier). "
            f"Upgrade your plan to add more senders."
        )

    # Insert new sender
    sender_id = new_id()
    db.execute("""
        INSERT INTO screened_senders (id, user_id, sender_email, sender_name, notify_sender)
        VALUES (?, ?, ?, ?, ?)
    """, [sender_id, user_id, sender_email, sender_name, int(notify_sender)])
    db.commit()

    row = db.execute("SELECT * FROM screened_senders WHERE id = ?", [sender_id]).fetchone()

    import json
    print("Status: 201")
    print("Content-Type: application/json")
    print()
    print(json.dumps(row_to_dict(row), default=str))
    return


def handle_patch(params):
    if "id" not in params:
        return error_response("Sender ID is required")

    db = get_db()
    sender = db.execute("SELECT * FROM screened_senders WHERE id = ?", [params["id"]]).fetchone()
    if not sender:
        return error_response("Sender not found", 404)

    body = read_body()
    updates = []
    values = []

    allowed_fields = ["is_active", "notify_sender", "sender_name"]
    for field in allowed_fields:
        if field in body:
            updates.append(f"{field} = ?")
            values.append(body[field])

    if not updates:
        return error_response("No valid fields to update")

    updates.append("updated_at = datetime('now')")
    values.append(params["id"])

    db.execute(f"UPDATE screened_senders SET {', '.join(updates)} WHERE id = ?", values)
    db.commit()

    row = db.execute("SELECT * FROM screened_senders WHERE id = ?", [params["id"]]).fetchone()
    return json_response(row_to_dict(row))


def handle_delete(params):
    if "id" not in params:
        return error_response("Sender ID is required")

    db = get_db()
    sender = db.execute("SELECT * FROM screened_senders WHERE id = ?", [params["id"]]).fetchone()
    if not sender:
        return error_response("Sender not found", 404)

    db.execute("DELETE FROM screened_senders WHERE id = ?", [params["id"]])
    db.commit()

    return json_response({"deleted": True, "id": params["id"]})


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
        elif method == "DELETE":
            handle_delete(params)
        else:
            error_response(f"Method {method} not allowed", 405)
    except Exception as e:
        error_response(f"Internal error: {str(e)}", 500)


if __name__ == "__main__":
    main()
