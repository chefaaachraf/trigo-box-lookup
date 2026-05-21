"""PostgreSQL backend — activé quand DATABASE_URL est défini."""
import os
import psycopg2
from psycopg2.extras import RealDictCursor


def _conn():
    url = os.environ["DATABASE_URL"]
    # Supabase exige SSL
    if "sslmode" not in url:
        url += "?sslmode=require"
    return psycopg2.connect(url)


def init():
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS manual_entries (
                ref         TEXT PRIMARY KEY,
                uc          TEXT NOT NULL,
                desc        TEXT DEFAULT '',
                emplacement TEXT DEFAULT ''
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id                  SERIAL PRIMARY KEY,
                datetime            TEXT,
                date                TEXT,
                time                TEXT,
                raw                 TEXT,
                ref                 TEXT,
                uc                  TEXT,
                status              TEXT,
                message             TEXT,
                image_url           TEXT,
                emplacement         TEXT,
                placement_image_url TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS image_urls (
                key  TEXT PRIMARY KEY,
                url  TEXT NOT NULL,
                kind TEXT NOT NULL
            )
        """)
        conn.commit()


# ── Manual entries ─────────────────────────────────────────────────────────────

def manual_list() -> list[dict]:
    with _conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT ref, uc, desc, emplacement FROM manual_entries ORDER BY ref")
        return [dict(r) for r in cur.fetchall()]


def manual_upsert(ref: str, uc: str, desc: str, emplacement: str) -> str:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM manual_entries WHERE ref = %s", (ref,))
        exists = cur.fetchone() is not None
        if exists:
            cur.execute(
                "UPDATE manual_entries SET uc=%s, desc=%s, emplacement=%s WHERE ref=%s",
                (uc, desc, emplacement, ref),
            )
        else:
            cur.execute(
                "INSERT INTO manual_entries (ref, uc, desc, emplacement) VALUES (%s,%s,%s,%s)",
                (ref, uc, desc, emplacement),
            )
        conn.commit()
    return "updated" if exists else "added"


def manual_delete(ref: str) -> bool:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM manual_entries WHERE ref = %s", (ref,))
        deleted = cur.rowcount
        conn.commit()
    return deleted > 0


# ── Scan history ───────────────────────────────────────────────────────────────

def history_insert(entry: dict) -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO scan_history
              (datetime, date, time, raw, ref, uc, status, message,
               image_url, emplacement, placement_image_url)
            VALUES (%(datetime)s, %(date)s, %(time)s, %(raw)s, %(ref)s, %(uc)s,
                    %(status)s, %(message)s, %(image_url)s, %(emplacement)s,
                    %(placement_image_url)s)
        """, entry)
        cur.execute("""
            DELETE FROM scan_history WHERE id NOT IN (
                SELECT id FROM scan_history ORDER BY id DESC LIMIT 2000
            )
        """)
        conn.commit()


def history_get(limit: int = 100, status: str = "", q: str = "", date: str = "") -> list[dict]:
    conds, params = [], []
    if status:
        conds.append("status = %s"); params.append(status)
    if date:
        conds.append("date = %s"); params.append(date)
    if q:
        conds.append("(ref ILIKE %s OR raw ILIKE %s OR uc ILIKE %s)")
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    params.append(limit)
    with _conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""
            SELECT datetime, date, time, raw, ref, uc, status, message,
                   image_url, emplacement, placement_image_url
            FROM scan_history {where}
            ORDER BY id DESC LIMIT %s
        """, params)
        return [dict(r) for r in cur.fetchall()]


def history_clear() -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM scan_history")
        conn.commit()


def history_count() -> int:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM scan_history")
        return cur.fetchone()[0]


# ── Image URLs ─────────────────────────────────────────────────────────────────

def image_set(key: str, url: str, kind: str) -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO image_urls (key, url, kind) VALUES (%s, %s, %s)
            ON CONFLICT (key) DO UPDATE SET url = EXCLUDED.url
        """, (key, url, kind))
        conn.commit()


def image_get(key: str) -> str | None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT url FROM image_urls WHERE key = %s", (key,))
        row = cur.fetchone()
        return row[0] if row else None
