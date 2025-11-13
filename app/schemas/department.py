from pydantic import BaseModel
from typing import Optional

class DepartmentBase(BaseModel):
    department_name: str
    manager_id: Optional[int] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = None
    manager_id: Optional[int] = None

class DepartmentResponse(DepartmentBase):
    id: int
    manager_name: Optional[str] = None
    
    class Config:
        from_attributes = True