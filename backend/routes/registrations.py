import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from database import get_db, query_one, execute
from models import RegistrationCreate

router = APIRouter()


@router.post("/registrations", status_code=201)
def create_registration(data: RegistrationCreate):
    conn = get_db()
    try:
        course = query_one(conn,
            "SELECT * FROM courses WHERE id = %s AND is_active = 1", (data.course_id,))
        if not course:
            raise HTTPException(status_code=404, detail="Kurz nenalezen")

        count = query_one(conn,
            "SELECT COUNT(*) AS cnt FROM registrations WHERE course_id = %s AND payment_status != 'cancelled'",
            (data.course_id,))
        if count["cnt"] >= course["capacity"]:
            raise HTTPException(status_code=400, detail="Kapacita kurzu je plná")

        existing = query_one(conn,
            "SELECT id FROM registrations WHERE course_id = %s AND email = %s AND payment_status != 'cancelled'",
            (data.course_id, data.email.lower()))
        if existing:
            raise HTTPException(status_code=400, detail="Na tento kurz jste již přihlášeni")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Vložíme přihlášku a získáme ID přes RETURNING
        cur = execute(conn, """
            INSERT INTO registrations
                (course_id, first_name, last_name, email, phone, notes, variable_symbol, registered_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.course_id,
            data.first_name.strip(), data.last_name.strip(),
            data.email.lower().strip(), data.phone.strip(), data.notes.strip(),
            "temp", now,
        ))
        new_id = cur.fetchone()["id"]

        # Variabilní symbol = rok + ID přihlášky (4 místa)
        variable_symbol = f"{datetime.now().year}{str(new_id).zfill(4)}"
        execute(conn, "UPDATE registrations SET variable_symbol = %s WHERE id = %s",
                (variable_symbol, new_id))
        conn.commit()

        reg = query_one(conn, "SELECT * FROM registrations WHERE id = %s", (new_id,))
        reg["bank_account"]  = os.getenv("BANK_ACCOUNT", "CZ00 0000 0000 0000 0000 0000")
        reg["course_name"]   = course["name"]
        reg["course_price"]  = course["price"]
        return reg

    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
