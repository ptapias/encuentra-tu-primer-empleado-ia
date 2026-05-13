#!/usr/bin/env python3
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sqlite3


ROOT = Path(__file__).resolve().parent
DB_FILE = ROOT / "crm.sqlite3"
JSONL_FILE = ROOT / "crm_leads.jsonl"
BACKUP_DIR = ROOT / "backups"


def backup_sqlite(source: Path, target: Path):
    source_conn = sqlite3.connect(source)
    try:
        target_conn = sqlite3.connect(target)
        try:
            source_conn.backup(target_conn)
        finally:
            target_conn.close()
    finally:
        source_conn.close()


def main():
    if not DB_FILE.exists():
        raise SystemExit(f"No existe {DB_FILE}")
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    db_target = BACKUP_DIR / f"crm-{stamp}.sqlite3"
    jsonl_target = BACKUP_DIR / f"crm-leads-{stamp}.jsonl"
    backup_sqlite(DB_FILE, db_target)
    copied = [str(db_target)]
    if JSONL_FILE.exists():
        shutil.copy2(JSONL_FILE, jsonl_target)
        copied.append(str(jsonl_target))
    print("\n".join(copied))


if __name__ == "__main__":
    main()

