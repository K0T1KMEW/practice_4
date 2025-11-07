from pydantic import BaseModel, Field
from typing import Optional

class DepartmentBase(BaseModel):
    department_name: str = Field(..., description="Название отдела")
    manager_id: Optional[int] = Field(..., description="ID управляющего отделом")

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Название отдела")
    manager_id: Optional[int] = Field(None, description="ID управляющего отделом")

class DepartmentResponse(DepartmentBase):
    id: int
    
    class Config:
        from_attributes = True