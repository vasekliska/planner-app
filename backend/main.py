import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from database import init_db
from routes.courses import router as courses_router
from routes.registrations import router as registrations_router
from routes.admin import router as admin_router

app = FastAPI(title="Planner API", docs_url="/api/docs", redoc_url=None)

init_db()

app.include_router(courses_router, prefix="/api")
app.include_router(registrations_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

FRONTEND = Path(__file__).parent.parent / "frontend"


@app.get("/")
def index():
    return FileResponse(str(FRONTEND / "index.html"))


@app.get("/kurz/{course_id}")
def course_page(course_id: int):
    return FileResponse(str(FRONTEND / "kurz.html"))


@app.get("/admin")
def admin_redirect():
    return RedirectResponse("/admin/")


app.mount("/static", StaticFiles(directory=str(FRONTEND / "static")), name="static")
app.mount("/admin", StaticFiles(directory=str(FRONTEND / "admin"), html=True), name="admin")
