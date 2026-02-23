"""
SQLite database manager for CMPC Role Recommender application.

Handles persistence of analyses, recommendations, feedback, and user data.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = Path(__file__).parent / "cmpc.db"


def _get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS analyses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            created_at      TEXT    NOT NULL,
            status          TEXT    NOT NULL DEFAULT 'en_proceso',
            similarity_threshold  REAL,
            classifier_threshold  REAL,
            model_used      TEXT,
            validation_recall     REAL,
            validation_precision  REAL,
            total_recommendations INTEGER DEFAULT 0,
            total_users     INTEGER DEFAULT 0,
            data_folder     TEXT,
            resumen_file    TEXT,
            user_filter     TEXT
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id     INTEGER NOT NULL,
            usuario         TEXT    NOT NULL,
            recommended_role TEXT   NOT NULL,
            confidence      REAL,
            count           INTEGER,
            avg_similarity  REAL,
            similar_users   TEXT,
            departamento    TEXT,
            funcion         TEXT,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            recommendation_id INTEGER NOT NULL,
            analysis_id     INTEGER NOT NULL,
            usuario         TEXT    NOT NULL,
            recommended_role TEXT   NOT NULL,
            is_useful       INTEGER NOT NULL,
            created_at      TEXT    NOT NULL,
            FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS users_analyzed (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id     INTEGER NOT NULL,
            usuario         TEXT    NOT NULL,
            departamento    TEXT,
            funcion         TEXT,
            n_roles         INTEGER DEFAULT 0,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_rec_analysis ON recommendations(analysis_id);
        CREATE INDEX IF NOT EXISTS idx_rec_usuario ON recommendations(usuario);
        CREATE INDEX IF NOT EXISTS idx_fb_analysis ON feedback(analysis_id);
        CREATE INDEX IF NOT EXISTS idx_users_analysis ON users_analyzed(analysis_id);
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Analyses CRUD
# ---------------------------------------------------------------------------

def create_analysis(
    name: str,
    similarity_threshold: float,
    classifier_threshold: float,
    model_used: str,
    data_folder: str = "",
    resumen_file: str = "",
    user_filter: str = "",
) -> int:
    """Create a new analysis record and return its id."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO analyses
           (name, created_at, status, similarity_threshold, classifier_threshold,
            model_used, data_folder, resumen_file, user_filter)
           VALUES (?, ?, 'en_proceso', ?, ?, ?, ?, ?, ?)""",
        (
            name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            similarity_threshold,
            classifier_threshold,
            model_used,
            data_folder,
            resumen_file,
            user_filter,
        ),
    )
    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return analysis_id


def update_analysis_results(
    analysis_id: int,
    recall: float,
    precision: float,
    total_recommendations: int,
    total_users: int,
    status: str = "completado",
):
    """Update an analysis with its results after pipeline finishes."""
    conn = _get_connection()
    conn.execute(
        """UPDATE analyses
           SET validation_recall = ?, validation_precision = ?,
               total_recommendations = ?, total_users = ?, status = ?
           WHERE id = ?""",
        (recall, precision, total_recommendations, total_users, status, analysis_id),
    )
    conn.commit()
    conn.close()


def update_analysis_status(analysis_id: int, status: str):
    """Update only the status of an analysis."""
    conn = _get_connection()
    conn.execute("UPDATE analyses SET status = ? WHERE id = ?", (status, analysis_id))
    conn.commit()
    conn.close()


def get_all_analyses() -> List[Dict]:
    """Return all analyses ordered by creation date descending."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM analyses ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_analysis_by_id(analysis_id: int) -> Optional[Dict]:
    """Return a single analysis by id."""
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_analysis(analysis_id: int):
    """Delete an analysis and all related data (cascade)."""
    conn = _get_connection()
    conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Recommendations CRUD
# ---------------------------------------------------------------------------

def save_recommendations(analysis_id: int, recommendations: List[Dict]):
    """Bulk insert recommendations for an analysis."""
    conn = _get_connection()
    conn.executemany(
        """INSERT INTO recommendations
           (analysis_id, usuario, recommended_role, confidence, count,
            avg_similarity, similar_users, departamento, funcion)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                analysis_id,
                r["usuario"],
                r["recommended_role"],
                r.get("confidence"),
                r.get("count"),
                r.get("avg_similarity"),
                r.get("similar_users", ""),
                r.get("departamento", ""),
                r.get("funcion", ""),
            )
            for r in recommendations
        ],
    )
    conn.commit()
    conn.close()


def get_recommendations(
    analysis_id: int,
    usuario_filter: str = "",
    limit: int = 50,
    offset: int = 0,
) -> tuple[List[Dict], int]:
    """Return paginated recommendations and total count for an analysis."""
    conn = _get_connection()

    where = "WHERE analysis_id = ?"
    params: list = [analysis_id]

    if usuario_filter:
        where += " AND usuario LIKE ?"
        params.append(f"%{usuario_filter}%")

    total = conn.execute(
        f"SELECT COUNT(*) FROM recommendations {where}", params
    ).fetchone()[0]

    rows = conn.execute(
        f"""SELECT * FROM recommendations {where}
            ORDER BY confidence DESC, count DESC
            LIMIT ? OFFSET ?""",
        params + [limit, offset],
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows], total


def get_all_recommendations(analysis_id: int) -> List[Dict]:
    """Return all recommendations for an analysis (no pagination)."""
    conn = _get_connection()
    rows = conn.execute(
        """SELECT * FROM recommendations
           WHERE analysis_id = ?
           ORDER BY confidence DESC, count DESC""",
        (analysis_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Feedback CRUD
# ---------------------------------------------------------------------------

def save_feedback_batch(feedbacks: List[Dict]):
    """Save a batch of feedback entries."""
    conn = _get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.executemany(
        """INSERT OR REPLACE INTO feedback
           (recommendation_id, analysis_id, usuario, recommended_role, is_useful, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (
                f["recommendation_id"],
                f["analysis_id"],
                f["usuario"],
                f["recommended_role"],
                1 if f["is_useful"] else 0,
                now,
            )
            for f in feedbacks
        ],
    )
    conn.commit()
    conn.close()


def get_feedback_for_analysis(analysis_id: int) -> List[Dict]:
    """Return all feedback entries for an analysis."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM feedback WHERE analysis_id = ? ORDER BY created_at DESC",
        (analysis_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_feedback_for_recommendation(recommendation_id: int) -> Optional[Dict]:
    """Return feedback for a specific recommendation, if any."""
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM feedback WHERE recommendation_id = ? ORDER BY created_at DESC LIMIT 1",
        (recommendation_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def export_feedback_to_csv(analysis_id: int, output_path: str):
    """Export feedback for an analysis to a CSV file."""
    import pandas as pd

    feedbacks = get_feedback_for_analysis(analysis_id)
    if not feedbacks:
        return False
    df = pd.DataFrame(feedbacks)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return True


def get_all_negative_feedback_pairs() -> set:
    """Return set of (usuario, recommended_role) globally marked as not useful (is_useful=0)."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT DISTINCT usuario, recommended_role FROM feedback WHERE is_useful = 0"
    ).fetchall()
    conn.close()
    return {(r["usuario"], r["recommended_role"]) for r in rows}


def export_all_feedback_as_training_data(output_path: str) -> int:
    """
    Export all feedback across all analyses as a training CSV compatible
    with the CatBoost classifier format.

    Output columns: DEPARTAMETNO, FUNCION, ROL, ASIGNADO (1=útil, 0=no útil)
    Returns: number of rows exported.
    """
    import pandas as pd

    conn = _get_connection()
    rows = conn.execute("""
        SELECT f.usuario, f.recommended_role, f.is_useful,
               u.departamento, u.funcion
        FROM feedback f
        LEFT JOIN users_analyzed u
               ON f.usuario = u.usuario AND f.analysis_id = u.analysis_id
    """).fetchall()
    conn.close()

    if not rows:
        return 0

    records = [
        {
            "DEPARTAMETNO": r["departamento"] or "",
            "FUNCION": r["funcion"] or "",
            "ROL": r["recommended_role"],
            "ASIGNADO": int(r["is_useful"]),
        }
        for r in rows
    ]
    df = pd.DataFrame(records).drop_duplicates(
        subset=["DEPARTAMETNO", "FUNCION", "ROL", "ASIGNADO"]
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return len(df)


# ---------------------------------------------------------------------------
# Users Analyzed CRUD
# ---------------------------------------------------------------------------

def save_users_analyzed(analysis_id: int, users: List[Dict]):
    """Bulk insert users analyzed for an analysis."""
    conn = _get_connection()
    conn.executemany(
        """INSERT INTO users_analyzed
           (analysis_id, usuario, departamento, funcion, n_roles)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (
                analysis_id,
                u["usuario"],
                u.get("departamento", ""),
                u.get("funcion", ""),
                u.get("n_roles", 0),
            )
            for u in users
        ],
    )
    conn.commit()
    conn.close()


def get_users_analyzed(
    analysis_id: int,
    search: str = "",
    limit: int = 50,
    offset: int = 0,
) -> tuple[List[Dict], int]:
    """Return paginated users analyzed and total count."""
    conn = _get_connection()

    where = "WHERE analysis_id = ?"
    params: list = [analysis_id]

    if search:
        where += " AND (usuario LIKE ? OR departamento LIKE ? OR funcion LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    total = conn.execute(
        f"SELECT COUNT(*) FROM users_analyzed {where}", params
    ).fetchone()[0]

    rows = conn.execute(
        f"""SELECT * FROM users_analyzed {where}
            ORDER BY usuario ASC
            LIMIT ? OFFSET ?""",
        params + [limit, offset],
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows], total


# Initialize database on module import
init_db()
