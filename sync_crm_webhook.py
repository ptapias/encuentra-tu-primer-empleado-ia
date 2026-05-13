#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from urllib import request


ROOT = Path(__file__).resolve().parent


def load_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except Exception:
        return fallback


def fetch_leads(db_path: Path, *, limit: int, status: str = "", since_updated_at: int = 0) -> list[dict]:
    if not db_path.exists():
        raise FileNotFoundError(f"No existe la base de datos: {db_path}")
    query = """
        SELECT id, email, created_at, updated_at, stage, status, facts_json, signals_json,
               outcome_json, transcript_json, feedback_json
        FROM leads
        WHERE (? = '' OR status = ?)
          AND updated_at >= ?
        ORDER BY updated_at DESC
        LIMIT ?
    """
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, (status, status, since_updated_at, limit)).fetchall()
    leads = []
    for row in rows:
        facts = load_json(row["facts_json"], {})
        outcome = load_json(row["outcome_json"], {})
        feedback = load_json(row["feedback_json"], None)
        transcript = load_json(row["transcript_json"], [])
        crm_summary = outcome.get("crm_summary") if isinstance(outcome, dict) else {}
        attribution = facts.get("attribution") if isinstance(facts, dict) else {}
        cta_interest = facts.get("cta_interest") if isinstance(facts, dict) else {}
        leads.append(
            {
                "id": row["id"],
                "email": row["email"] or "",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "stage": row["stage"],
                "status": row["status"],
                "facts": facts,
                "signals": load_json(row["signals_json"], {}),
                "outcome": outcome,
                "feedback": feedback,
                "transcript": transcript,
                "crm_summary": crm_summary or {},
                "attribution": attribution or {},
                "cta_interest": cta_interest or {},
                "turns": len([m for m in transcript if isinstance(m, dict) and m.get("role") == "user"]),
            }
        )
    return leads


def record_sync_event(db_path: Path, lead_id: str, payload: dict):
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO events (lead_id, event, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (
                lead_id,
                "crm_webhook_snapshot_synced",
                json.dumps(payload, ensure_ascii=False),
                int(time.time()),
            ),
        )


def send_snapshot(url: str, secret: str, lead: dict, *, include_transcript: bool, timeout: float) -> tuple[bool, str]:
    snapshot = dict(lead)
    if not include_transcript:
        snapshot.pop("transcript", None)
    body = {
        "event": "lead_snapshot_synced",
        "lead_id": lead["id"],
        "created_at": int(time.time()),
        "payload": {"lead": snapshot},
    }
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "primer-empleado-ia-sync/1.0",
        "X-CRM-Event": "lead_snapshot_synced",
        "X-CRM-Lead-ID": lead["id"],
    }
    if secret:
        headers["X-CRM-Webhook-Secret"] = secret
    req = request.Request(url, data=encoded, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            if response.status >= 400:
                return False, f"HTTP {response.status}"
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza leads existentes del CRM local hacia un webhook externo")
    parser.add_argument("--db", default=str(ROOT / "crm.sqlite3"))
    parser.add_argument("--url", default=os.environ.get("CRM_WEBHOOK_URL", "").strip())
    parser.add_argument("--secret", default=os.environ.get("CRM_WEBHOOK_SECRET", "").strip())
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("CRM_WEBHOOK_TIMEOUT", "5")))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--status", default="", help="Opcional: sincronizar solo leads con este estado")
    parser.add_argument("--since-updated-at", type=int, default=0)
    parser.add_argument("--no-transcript", action="store_true", help="No incluir conversación completa en el webhook")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not args.url and not args.dry_run:
        print(json.dumps({"ok": False, "error": "Falta --url o CRM_WEBHOOK_URL"}, ensure_ascii=False, indent=2))
        return 2

    leads = fetch_leads(db_path, limit=args.limit, status=args.status, since_updated_at=args.since_updated_at)
    results = []
    failures = []
    for lead in leads:
        if args.dry_run:
            ok, message = True, "dry_run"
        else:
            ok, message = send_snapshot(
                args.url,
                args.secret,
                lead,
                include_transcript=not args.no_transcript,
                timeout=max(1.0, args.timeout),
            )
            if ok:
                record_sync_event(db_path, lead["id"], {"url": args.url, "status": lead["status"], "message": message})
        item = {"lead_id": lead["id"], "email": lead["email"], "status": lead["status"], "ok": ok, "message": message}
        results.append(item)
        if not ok:
            failures.append(item)

    output = {
        "ok": not failures,
        "dry_run": args.dry_run,
        "count": len(leads),
        "sent": len([item for item in results if item["ok"] and item["message"] != "dry_run"]),
        "failures": failures,
        "results": results,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
