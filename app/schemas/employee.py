from pydantic import BaseModel
from typing import Optional
from datetime import date

class EmployeeBase(BaseModel):
    username: str
    date_of_birth: date
    department_id: int
    role_id: Optional[int] = None
    salary: int
    bet: int
    status: str = "active"
    date_of_admission: date
    photo: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    username: Optional[str] = None
    date_of_birth: Optional[date] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    salary: Optional[int] = None
    bet: Optional[int] = None
    status: Optional[str] = None
    date_of_admission: Optional[date] = None
    photo: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: int
    department_name: Optional[str] = None
    role_name: Optional[str] = None
    
    class Config:
        from_attributes = True