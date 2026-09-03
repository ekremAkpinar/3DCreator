from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from .config import DB_PATH, ensure_dirs


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                prompt TEXT NOT NULL DEFAULT '',
                model_family TEXT NOT NULL DEFAULT 'unknown',
                classification_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS generations (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                status TEXT NOT NULL,
                quality TEXT NOT NULL,
                source_image TEXT NOT NULL,
                output_file TEXT,
                comfy_prompt_id TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_id TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                note TEXT NOT NULL DEFAULT '',
                approved_for_learning INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(generation_id) REFERENCES generations(id)
            );
            """
        )

        project_columns = {row["name"] for row in conn.execute("PRAGMA table_info(projects)")}
        if "model_family" not in project_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN model_family TEXT NOT NULL DEFAULT 'unknown'")
        if "classification_json" not in project_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN classification_json TEXT NOT NULL DEFAULT '{}'")

        generation_columns = {row["name"] for row in conn.execute("PRAGMA table_info(generations)")}
        if "mode" not in generation_columns:
            conn.execute("ALTER TABLE generations ADD COLUMN mode TEXT NOT NULL DEFAULT 'single'")
        if "source_images_json" not in generation_columns:
            conn.execute("ALTER TABLE generations ADD COLUMN source_images_json TEXT NOT NULL DEFAULT '[]'")
        if "repaired_file" not in generation_columns:
            conn.execute("ALTER TABLE generations ADD COLUMN repaired_file TEXT")
        if "repair_status" not in generation_columns:
            conn.execute("ALTER TABLE generations ADD COLUMN repair_status TEXT NOT NULL DEFAULT 'none'")
        if "repair_log" not in generation_columns:
            conn.execute("ALTER TABLE generations ADD COLUMN repair_log TEXT NOT NULL DEFAULT ''")

        feedback_columns = {row["name"] for row in conn.execute("PRAGMA table_info(feedback)")}
        if "issues_json" not in feedback_columns:
            conn.execute("ALTER TABLE feedback ADD COLUMN issues_json TEXT NOT NULL DEFAULT '[]'")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_family ON projects(model_family)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_generations_project ON generations(project_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_generation ON feedback(generation_id)")


def rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]
