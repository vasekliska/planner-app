import os
import psycopg2
import psycopg2.extras


def get_db() -> psycopg2.extensions.connection:
    url = os.environ["DATABASE_URL"]
    # Render.com vrací postgres://, psycopg2 vyžaduje postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


def query_all(conn, sql: str, params: tuple = ()) -> list[dict]:
    """Spustí SELECT a vrátí všechny řádky jako list diktů."""
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def query_one(conn, sql: str, params: tuple = ()) -> dict | None:
    """Spustí SELECT a vrátí jeden řádek jako dict, nebo None."""
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def execute(conn, sql: str, params: tuple = ()):
    """Spustí INSERT/UPDATE/DELETE a vrátí cursor (pro RETURNING)."""
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id             SERIAL  PRIMARY KEY,
            name           TEXT    NOT NULL,
            date           TEXT    NOT NULL,
            time           TEXT    NOT NULL,
            location       TEXT    NOT NULL,
            description    TEXT    NOT NULL DEFAULT '',
            type           TEXT    NOT NULL DEFAULT 'jednorázový',
            recurring_info TEXT    NOT NULL DEFAULT '',
            capacity       INTEGER NOT NULL DEFAULT 10,
            price          REAL    NOT NULL DEFAULT 0,
            is_active      INTEGER NOT NULL DEFAULT 1,
            created_at     TEXT    NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id              SERIAL  PRIMARY KEY,
            course_id       INTEGER NOT NULL REFERENCES courses(id),
            first_name      TEXT    NOT NULL,
            last_name       TEXT    NOT NULL,
            email           TEXT    NOT NULL,
            phone           TEXT    NOT NULL DEFAULT '',
            payment_status  TEXT    NOT NULL DEFAULT 'pending',
            variable_symbol TEXT    NOT NULL,
            notes           TEXT    NOT NULL DEFAULT '',
            registered_at   TEXT    NOT NULL
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
