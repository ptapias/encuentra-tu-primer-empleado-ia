#!/usr/bin/env python3
import sqlite3
import tempfile
from pathlib import Path

import backup_crm


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_backup_creates_sqlite_and_jsonl_copy():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-backup-test-") as tmp_dir:
        root = Path(tmp_dir)
        db_file = root / "crm.sqlite3"
        jsonl_file = root / "crm_leads.jsonl"
        backup_dir = root / "backups"

        with sqlite3.connect(db_file) as conn:
            conn.execute("CREATE TABLE leads (id TEXT PRIMARY KEY, email TEXT)")
            conn.execute("INSERT INTO leads (id, email) VALUES (?, ?)", ("lead-1", "test@example.com"))
        jsonl_file.write_text('{"lead_id":"lead-1"}\n', encoding="utf-8")

        original_db = backup_crm.DB_FILE
        original_jsonl = backup_crm.JSONL_FILE
        original_backup_dir = backup_crm.BACKUP_DIR
        try:
            backup_crm.DB_FILE = db_file
            backup_crm.JSONL_FILE = jsonl_file
            backup_crm.BACKUP_DIR = backup_dir
            backup_crm.main()
        finally:
            backup_crm.DB_FILE = original_db
            backup_crm.JSONL_FILE = original_jsonl
            backup_crm.BACKUP_DIR = original_backup_dir

        db_backups = list(backup_dir.glob("crm-*.sqlite3"))
        jsonl_backups = list(backup_dir.glob("crm-leads-*.jsonl"))
        assert_true(len(db_backups) == 1, "Debe crear una copia SQLite")
        assert_true(len(jsonl_backups) == 1, "Debe crear una copia JSONL")
        with sqlite3.connect(db_backups[0]) as conn:
            row = conn.execute("SELECT email FROM leads WHERE id = ?", ("lead-1",)).fetchone()
        assert_true(row and row[0] == "test@example.com", "La copia SQLite no conserva los datos")
        assert_true(jsonl_backups[0].read_text(encoding="utf-8") == '{"lead_id":"lead-1"}\n', "La copia JSONL no conserva el contenido")


if __name__ == "__main__":
    test_backup_creates_sqlite_and_jsonl_copy()
    print("backup_crm ok")
