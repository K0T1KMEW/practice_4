from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging

from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.db.database import db_manager

from app.core.dependencies import require_admin, require_employee_or_admin
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee: EmployeeCreate,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        employee_data = employee.model_dump()
        new_employee = await db_manager.create_employee(employee_data)
        
        if not new_employee:
            raise HTTPException(status_code=400, detail="Не удалось создать сотрудника")
        
        return new_employee
    except Exception as e:
        logger.error(f"Ошибка при создании сотрудника: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: Optional[str] = None,
    status: Optional[str] = None,
    job_title: Optional[str] = None,
    min_salary: Optional[int] = Query(None, ge=0),
    max_salary: Optional[int] = Query(None, ge=0),
    search: Optional[str] = None,
    current_user: User = Depends(require_employee_or_admin)
):
    await db_manager.create_connection()
    try:
        employees = await db_manager.get_all_employees(
            skip=skip,
            limit=limit,
            department=department,
            status=status,
            job_title=job_title,
            min_salary=min_salary,
            max_salary=max_salary,
            search=search
        )
        return employees
    finally:
        await db_manager.close_connection()

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: int):
    await db_manager.create_connection()
    try:
        employee = await db_manager.get_employee_by_id(employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")
        return employee
    finally:
        await db_manager.close_connection()

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: int, employee_update: EmployeeUpdate):
    await db_manager.create_connection()
    try:
        update_data = employee_update.model_dump(exclude_unset=True)
        
        success = await db_manager.update_employee(employee_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Сотрудник не найден или данные не изменились")
        
        updated_employee = await db_manager.get_employee_by_id(employee_id)
        return updated_employee
    finally:
        await db_manager.close_connection()

@router.delete("/{employee_id}")
async def delete_employee(employee_id: int):
    await db_manager.create_connection()
    try:
        success = await db_manager.delete_employee(employee_id)
        if not success:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")
        return {"message": "Сотрудник успешно удален"}
    finally:
        await db_manager.close_connection()