#!/usr/bin/env python3
"""Verifica que /api/chat acepte rewind_to_turn y trunque el transcript del lead."""
import json
import os
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

BASE = os.environ.get("BASE", "http://localhost:8787")


def post(path, payload):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def main() -> int:
    status, data = post("/api/session", {})
    assert status == 200, f"session create failed: {status} {data}"
    lead_id = data["lead_id"]

    for txt in ["primero", "segundo", "tercero"]:
        try:
            status, _ = post("/api/chat", {"lead_id": lead_id, "message": txt})
        except urllib.error.HTTPError as e:
            status = e.code
        assert status in (200, 429), f"chat returned {status}"
        if status == 429:
            print(json.dumps({"ok": True, "skipped": True, "reason": "ai busy during setup"}))
            return 0
        time.sleep(0.3)

    db_path = Path(os.environ.get("CRM_DB", "crm.sqlite3"))
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT transcript_json FROM leads WHERE id = ?", (lead_id,)).fetchone()
    finally:
        con.close()
    assert row, "lead not in CRM"
    transcript_pre = json.loads(row[0])
    user_turns_pre = [m for m in transcript_pre if m.get("role") == "user"]
    assert len(user_turns_pre) == 3, f"expected 3 user turns, got {len(user_turns_pre)}"

    try:
        status, _ = post("/api/chat", {"lead_id": lead_id, "message": "rewind y nuevo", "rewind_to_turn": 1})
    except urllib.error.HTTPError as e:
        status = e.code
    assert status in (200, 429), f"rewind chat returned {status}"
    if status == 429:
        print(json.dumps({"ok": True, "skipped": True, "reason": "ai busy after rewind"}))
        return 0

    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT transcript_json FROM leads WHERE id = ?", (lead_id,)).fetchone()
    finally:
        con.close()
    transcript_post = json.loads(row[0])
    user_turns_post = [m for m in transcript_post if m.get("role") == "user"]
    assert len(user_turns_post) == 2, f"expected 2 user turns after rewind, got {len(user_turns_post)}"
    assert user_turns_post[0]["content"] == "primero", f"expected first turn preserved, got {user_turns_post[0]}"
    assert user_turns_post[-1]["content"] == "rewind y nuevo"

    print(json.dumps({"ok": True, "lead_id": lead_id, "user_turns_post": len(user_turns_post)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
