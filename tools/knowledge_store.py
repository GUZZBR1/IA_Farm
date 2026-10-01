"""Transactional canonical record snapshots and append-only SQLite audit events."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from tools.knowledge_schema import (
    validate_audit_event, validate_record, record_sha256,
)
from tools.knowledge_lifecycle import validate_audit_chain


class KnowledgeStore:
    """Small local store; identity authentication remains the caller's duty."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS knowledge_records (
                    record_id TEXT PRIMARY KEY,
                    record_json TEXT NOT NULL,
                    audit_head TEXT NOT NULL,
                    revision INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS knowledge_audit_events (
                    event_id TEXT PRIMARY KEY,
                    record_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    event_json TEXT NOT NULL,
                    event_sha256 TEXT NOT NULL UNIQUE,
                    UNIQUE(record_id, revision),
                    FOREIGN KEY(record_id) REFERENCES knowledge_records(record_id)
                );
                CREATE TRIGGER IF NOT EXISTS knowledge_audit_no_update
                BEFORE UPDATE ON knowledge_audit_events BEGIN
                    SELECT RAISE(ABORT, 'knowledge audit events are append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS knowledge_audit_no_delete
                BEFORE DELETE ON knowledge_audit_events BEGIN
                    SELECT RAISE(ABORT, 'knowledge audit events are append-only');
                END;
            """)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, isolation_level="IMMEDIATE")
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _dump(value: dict[str, Any]) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def persist(self, record: dict[str, Any], event: dict[str, Any], *,
                expected_head: str | None) -> None:
        """Atomically append one event and update its snapshot with CAS protection."""
        validate_record(record)
        validate_audit_event(event)
        if (event["record_id"] != record["record_id"] or event["revision"] != record["revision"]
                or event["after_sha256"] != record_sha256(record)
                or event["event_sha256"] != record["audit_head"]):
            raise ValueError("event does not bind the supplied record snapshot")
        with self._connect() as connection:
            prior_rows = connection.execute(
                "SELECT event_json FROM knowledge_audit_events WHERE record_id=? ORDER BY revision",
                (record["record_id"],)).fetchall()
            prior_events = [json.loads(row["event_json"]) for row in prior_rows]
            current = connection.execute(
                "SELECT record_json, audit_head, revision FROM knowledge_records WHERE record_id=?",
                (record["record_id"],)).fetchone()
            if current is None:
                if expected_head is not None or event["from_status"] is not None or event["revision"] != 1:
                    raise ValueError("record creation must start at revision 1 without a prior head")
                if event["before_sha256"] is not None or event["previous_event_sha256"] is not None:
                    raise ValueError("initial event cannot claim a previous record or event")
                validate_audit_chain([event], record)
                connection.execute("INSERT INTO knowledge_records VALUES (?, ?, ?, ?)",
                                   (record["record_id"], self._dump(record), record["audit_head"], record["revision"]))
            else:
                previous = json.loads(current["record_json"])
                if expected_head != current["audit_head"]:
                    raise ValueError("stale audit head; refusing concurrent or reordered transition")
                if (event["revision"] != current["revision"] + 1
                        or event["previous_event_sha256"] != current["audit_head"]
                        or event["before_sha256"] != record_sha256(previous)):
                    raise ValueError("transition event does not continue the stored audit chain")
                validate_audit_chain([*prior_events, event], record)
                changed = connection.execute(
                    "UPDATE knowledge_records SET record_json=?, audit_head=?, revision=? WHERE record_id=? AND audit_head=?",
                    (self._dump(record), record["audit_head"], record["revision"], record["record_id"], expected_head),
                ).rowcount
                if changed != 1:
                    raise ValueError("audit head changed during transition")
            connection.execute("INSERT INTO knowledge_audit_events VALUES (?, ?, ?, ?, ?)",
                               (event["event_id"], event["record_id"], event["revision"],
                                self._dump(event), event["event_sha256"]))

    def get(self, record_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT record_json FROM knowledge_records WHERE record_id=?",
                                     (record_id,)).fetchone()
        return json.loads(row["record_json"]) if row else None

    def events(self, record_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT event_json FROM knowledge_audit_events WHERE record_id=? ORDER BY revision",
                (record_id,)).fetchall()
        events = [json.loads(row["event_json"]) for row in rows]
        validate_audit_chain(events, self.get(record_id))
        return events
