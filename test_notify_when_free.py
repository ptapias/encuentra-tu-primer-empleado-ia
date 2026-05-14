#!/usr/bin/env python3
"""Verifica que /api/notify-when-free registre el email y devuelva ok."""
import json
import os
import sqlite3
import sys
import urllib.error
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
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def main() -> int:
    status, data = post("/api/session", {})
    assert status == 200, f"session failed: {status}"
    lead_id = data["lead_id"]

    status, data = post("/api/notify-when-free", {"lead_id": lead_id, "email": "test+notify@example.com"})
    assert status == 200, f"notify-when-free returned {status}: {data}"
    assert data.get("ok") is True

    db_path = Path(os.environ.get("CRM_DB", "crm.sqlite3"))
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT payload_json FROM events WHERE lead_id = ? AND event = ?",
            (lead_id, "notify_when_free"),
        ).fetchone()
    finally:
        con.close()
    assert row, "notify_when_free event not stored"
    payload = json.loads(row[0])
    assert payload.get("email") == "test+notify@example.com"

    # Email inválido debe ser rechazado
    status, data = post("/api/notify-when-free", {"lead_id": lead_id, "email": "no-arroba"})
    assert status == 400, f"invalid email should 400, got {status}"

    print(json.dumps({"ok": True, "lead_id": lead_id}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
