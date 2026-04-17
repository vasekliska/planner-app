from fastapi import APIRouter, HTTPException
from database import get_db, query_all, query_one

router = APIRouter()


@router.get("/courses")
def list_courses():
    conn = get_db()
    try:
        return query_all(conn, """
            SELECT c.*,
                   COUNT(CASE WHEN r.payment_status != 'cancelled' THEN 1 END) AS registered_count
            FROM courses c
            LEFT JOIN registrations r ON r.course_id = c.id
            WHERE c.is_active = 1
            GROUP BY c.id
            ORDER BY c.date ASC, c.time ASC
        """)
    finally:
        conn.close()


@router.get("/courses/{course_id}")
def get_course(course_id: int):
    conn = get_db()
    try:
        course = query_one(conn,
            "SELECT * FROM courses WHERE id = %s AND is_active = 1", (course_id,))
        if not course:
            raise HTTPException(status_code=404, detail="Kurz nenalezen")

        row = query_one(conn,
            "SELECT COUNT(*) AS cnt FROM registrations WHERE course_id = %s AND payment_status != 'cancelled'",
            (course_id,))
        course["registered_count"] = row["cnt"]
        return course
    finally:
        conn.close()
