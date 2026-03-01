#!/usr/bin/env python3
"""
GraceBox — Email Logs API
Handles activity log creation and retrieval.

GET    ?user_id=X                    → List recent logs (paginated)
       &limit=20&offset=0           → Pagination
       &sender_id=X                 → Filter by sender
       &rewritten_only=1            → Filter rewritten only
POST                                → Create log entry
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import (get_db, new_id, row_to_dict, rows_to_list, json_response,
                error_response, read_body, parse_query)

def handle_get(params):
    if "user_id" not in params:
        return error_response("user_id is required")

    user_id = params["user_id"]
    limit = min(int(params.get("limit", 20)), 100)
    offset = int(params.get("offset", 0))

    db = get_db()

    # Verify user exists
    user = db.execute("SELECT id FROM users WHERE id = ?", [user_id]).fetchone()
    if not user:
        return error_response("User not found", 404)

    # Build query with optional filters
    where_clauses = ["el.user_id = ?"]
    query_values = [user_id]

    if "sender_id" in params:
        where_clauses.append("el.screened_sender_id = ?")
        query_values.append(params["sender_id"])

    if params.get("rewritten_only") == "1":
        where_clauses.append("el.was_rewritten = 1")

    where_sql = " AND ".join(where_clauses)

    # Get total count
    count = db.execute(f"""
        SELECT COUNT(*) as total FROM email_logs el WHERE {where_sql}
    """, query_values).fetchone()["total"]

    # Get paginated results with sender email joined
    rows = db.execute(f"""
        SELECT el.*, ss.sender_email, ss.sender_name
        FROM email_logs el
        LEFT JOIN screened_senders ss ON el.screened_sender_id = ss.id
        WHERE {where_sql}
        ORDER BY el.processed_at DESC
        LIMIT ? OFFSET ?
    """, query_values + [limit, offset]).fetchall()

    return json_response({
        "logs": rows_to_list(rows),
        "total": count,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < count
    })


def handle_post():
    body = read_body()

    required_fields = ["user_id", "original_subject"]
    for field in required_fields:
        if not body.get(field):
            return error_response(f"{field} is required")

    db = get_db()

    # Verify user exists
    user = db.execute("SELECT * FROM users WHERE id = ?", [body["user_id"]]).fetchone()
    if not user:
        return error_response("User not found", 404)

    log_id = new_id()

    db.execute("""
        INSERT INTO email_logs
        (id, user_id, screened_sender_id, original_subject, original_body,
         rewritten_body, tone_score, tone_reason, was_rewritten, sender_notified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        log_id,
        body["user_id"],
        body.get("screened_sender_id"),
        body.get("original_subject", ""),
        body.get("original_body", ""),
        body.get("rewritten_body", ""),
        float(body.get("tone_score", 0.0)),
        body.get("tone_reason", ""),
        int(body.get("was_rewritten", 0)),
        int(body.get("sender_notified", 0)),
    ])

    # Update counters
    if body.get("screened_sender_id"):
        db.execute("""
            UPDATE screened_senders
            SET emails_screened_count = emails_screened_count + 1,
                updated_at = datetime('now')
            WHERE id = ?
        """, [body["screened_sender_id"]])

    db.execute("""
        UPDATE users
        SET emails_processed_this_month = emails_processed_this_month + 1,
            updated_at = datetime('now')
        WHERE id = ?
    """, [body["user_id"]])

    db.commit()

    row = db.execute("SELECT * FROM email_logs WHERE id = ?", [log_id]).fetchone()

    import json
    print("Status: 201")
    print("Content-Type: application/json")
    print()
    print(json.dumps(row_to_dict(row), default=str))
    return


def main():
    method = os.environ.get("REQUEST_METHOD", "GET")
    params = parse_query()

    try:
        if method == "GET":
            handle_get(params)
        elif method == "POST":
            handle_post()
        else:
            error_response(f"Method {method} not allowed", 405)
    except Exception as e:
        error_response(f"Internal error: {str(e)}", 500)


if __name__ == "__main__":
    main()
