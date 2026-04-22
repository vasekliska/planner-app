import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Header
from database import get_db, query_all, query_one, execute
from models import CourseCreate, CourseUpdate, PaymentStatusUpdate, AdminRegistrationCreate

router = APIRouter()

VALID_PAYMENT_STATUSES = ("pending", "paid", "cancelled")


def require_admin(x_admin_token: str = Header(None)) -> str:
    expected = os.getenv("ADMIN_TOKEN", "admin123")
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Neautorizovaný přístup")
    return x_admin_token


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/admin/login")
def admin_login(_: str = Depends(require_admin)):
    return {"ok": True}


# ── Courses ───────────────────────────────────────────────────────────────────

@router.get("/admin/courses")
def admin_list_courses(_: str = Depends(require_admin)):
    conn = get_db()
    try:
        return query_all(conn, """
            SELECT c.*,
                   COUNT(CASE WHEN r.payment_status != 'cancelled' THEN 1 END) AS registered_count
            FROM courses c
            LEFT JOIN registrations r ON r.course_id = c.id
            GROUP BY c.id
            ORDER BY c.date DESC, c.time DESC
        """)
    finally:
        conn.close()


@router.post("/admin/courses", status_code=201)
def admin_create_course(data: CourseCreate, _: str = Depends(require_admin)):
    conn = get_db()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = execute(conn, """
            INSERT INTO courses
                (name, date, time, location, description, type, recurring_info, capacity, price, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.name.strip(), data.date, data.time.strip(),
            data.location.strip(), data.description.strip(),
            data.type, data.recurring_info.strip(),
            data.capacity, data.price, now,
        ))
        new_id = cur.fetchone()["id"]
        conn.commit()
        return query_one(conn, "SELECT * FROM courses WHERE id = %s", (new_id,))
    finally:
        conn.close()


@router.put("/admin/courses/{course_id}")
def admin_update_course(course_id: int, data: CourseUpdate, _: str = Depends(require_admin)):
    conn = get_db()
    try:
        if not query_one(conn, "SELECT id FROM courses WHERE id = %s", (course_id,)):
            raise HTTPException(status_code=404, detail="Kurz nenalezen")
        execute(conn, """
            UPDATE courses
            SET name=%s, date=%s, time=%s, location=%s, description=%s, type=%s,
                recurring_info=%s, capacity=%s, price=%s, is_active=%s
            WHERE id=%s
        """, (
            data.name.strip(), data.date, data.time.strip(),
            data.location.strip(), data.description.strip(),
            data.type, data.recurring_info.strip(),
            data.capacity, data.price,
            1 if data.is_active else 0,
            course_id,
        ))
        conn.commit()
        return query_one(conn, "SELECT * FROM courses WHERE id = %s", (course_id,))
    finally:
        conn.close()


@router.delete("/admin/courses/{course_id}")
def admin_deactivate_course(course_id: int, _: str = Depends(require_admin)):
    conn = get_db()
    try:
        execute(conn, "UPDATE courses SET is_active = 0 WHERE id = %s", (course_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


# ── Registrations ─────────────────────────────────────────────────────────────

@router.post("/admin/registrations", status_code=201)
def admin_create_registration(data: AdminRegistrationCreate, _: str = Depends(require_admin)):
    if data.payment_status not in VALID_PAYMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Neplatný stav platby")
    conn = get_db()
    try:
        course = query_one(conn, "SELECT * FROM courses WHERE id = %s", (data.course_id,))
        if not course:
            raise HTTPException(status_code=404, detail="Kurz nenalezen")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = execute(conn, """
            INSERT INTO registrations
                (course_id, first_name, last_name, email, phone, notes, payment_status, variable_symbol, registered_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.course_id,
            data.first_name.strip(), data.last_name.strip(),
            data.email.lower().strip(), data.phone.strip(), data.notes.strip(),
            data.payment_status, "temp", now,
        ))
        new_id = cur.fetchone()["id"]

        variable_symbol = f"{datetime.now().year}{str(new_id).zfill(4)}"
        execute(conn, "UPDATE registrations SET variable_symbol = %s WHERE id = %s",
                (variable_symbol, new_id))
        conn.commit()

        reg = query_one(conn, "SELECT * FROM registrations WHERE id = %s", (new_id,))
        reg["bank_account"] = os.getenv("BANK_ACCOUNT", "CZ00 0000 0000 0000 0000 0000")
        reg["course_name"]  = course["name"]
        reg["course_price"] = course["price"]
        return reg
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@router.get("/admin/registrations")
def admin_list_registrations(_: str = Depends(require_admin)):
    conn = get_db()
    try:
        return query_all(conn, """
            SELECT r.*,
                   c.name  AS course_name,
                   c.date  AS course_date,
                   c.price AS course_price
            FROM registrations r
            JOIN courses c ON c.id = r.course_id
            ORDER BY r.registered_at DESC
        """)
    finally:
        conn.close()


@router.patch("/admin/registrations/{reg_id}/payment")
def admin_update_payment(
    reg_id: int, data: PaymentStatusUpdate, _: str = Depends(require_admin)
):
    if data.payment_status not in VALID_PAYMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Neplatný stav platby")
    conn = get_db()
    try:
        if not query_one(conn, "SELECT id FROM registrations WHERE id = %s", (reg_id,)):
            raise HTTPException(status_code=404, detail="Přihláška nenalezena")
        execute(conn, "UPDATE registrations SET payment_status = %s WHERE id = %s",
                (data.payment_status, reg_id))
        conn.commit()
        return query_one(conn, "SELECT * FROM registrations WHERE id = %s", (reg_id,))
    finally:
        conn.close()


@router.delete("/admin/registrations/{reg_id}")
def admin_delete_registration(reg_id: int, _: str = Depends(require_admin)):
    conn = get_db()
    try:
        execute(conn, "DELETE FROM registrations WHERE id = %s", (reg_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()
