from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class EmployeeBase(BaseModel):
    username: str = Field(..., description="ФИО сотрудника")
    date_of_birth: str = Field(..., description="Дата рождения в формате YYYY-MM-DD")
    status: str = Field(..., description="Статус: active, vacation, fired, sick")
    department: str = Field(..., description="Отдел")
    job_title: str = Field(..., description="Должность")
    bet: int = Field(..., ge=0, le=2, description="Ставка (0-2)")
    salary: int = Field(..., ge=0, description="Зарплата")
    date_of_admission: str = Field(..., description="Дата приема в формате YYYY-MM-DD")
    department_id: Optional[int] = Field(None, description="ID отдела")
    photo: Optional[str] = Field(None, description="URL фотографии")

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    username: Optional[str] = None
    date_of_birth: Optional[str] = None
    status: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    bet: Optional[int] = None
    salary: Optional[int] = None
    date_of_admission: Optional[str] = None
    department_id: Optional[int] = None
    photo: Optional[str] = None
    
class EmployeeResponse(EmployeeBase):
    id: int
    
    class Config:
        from_attributes = True