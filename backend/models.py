from pydantic import BaseModel
from typing import Optional


class CourseCreate(BaseModel):
    name: str
    date: str
    time: str
    location: str
    description: str = ""
    type: str = "jednorázový"
    recurring_info: str = ""
    capacity: int
    price: float = 0.0


class CourseUpdate(CourseCreate):
    is_active: bool = True


class RegistrationCreate(BaseModel):
    course_id: int
    first_name: str
    last_name: str
    email: str
    phone: str = ""
    notes: str = ""


class AdminRegistrationCreate(BaseModel):
    course_id: int
    first_name: str
    last_name: str
    email: str
    phone: str = ""
    notes: str = ""
    payment_status: str = "pending"


class PaymentStatusUpdate(BaseModel):
    payment_status: str
