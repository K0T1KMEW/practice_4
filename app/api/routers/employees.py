from fastapi import APIRouter, Depends, Query
from typing import Optional, List
import logging

from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.db.database import db_manager
from app.core.dependencies import require_admin
from app.models.user import User
from app.core.config import DefaultResponse
from app.core.converters import employee_to_response, employees_to_response_list

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=DefaultResponse[EmployeeResponse])
async def create_employee(
    employee: EmployeeCreate,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        employee_data = employee.model_dump()
        
        department = await db_manager.departments.get_by_id(employee_data['department_id'])
        if not department:
            return DefaultResponse(error=True, message="Указанный отдел не существует")
            
        role = await db_manager.roles.get_by_id(employee_data['role_id'])
        if not role:
            return DefaultResponse(error=True, message="Указанная должность не существует")
        
        exists = await db_manager.employees.check_employee_exists(
            employee_data['username'], 
            employee_data['date_of_birth']
        )
        
        if exists:
            return DefaultResponse(
                error=True, 
                message="Сотрудник с таким ФИО и датой рождения уже существует"
            )
        
        new_employee = await db_manager.employees.create(employee_data)
        
        if not new_employee:
            return DefaultResponse(error=True, message="Не удалось создать сотрудника")
        
        employee_response = employee_to_response(new_employee)
        
        return DefaultResponse(error=False, message="Сотрудник успешно создан", payload=employee_response)
    except Exception as e:
        logger.error(f"Ошибка при создании сотрудника: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.get("/", response_model=DefaultResponse[List[EmployeeResponse]])
async def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    role_id: Optional[int] = None,
    min_salary: Optional[int] = Query(None, ge=0),
    max_salary: Optional[int] = Query(None, ge=0),
    search: Optional[str] = None,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        employees = await db_manager.employees.get_all_employees(
            skip=skip,
            limit=limit,
            department_id=department_id,
            status=status,
            role_id=role_id,
            min_salary=min_salary,
            max_salary=max_salary,
            search=search
        )
        
        employees_response = employees_to_response_list(employees)
        
        return DefaultResponse(error=False, message="OK", payload=employees_response)
    except Exception as e:
        logger.error(f"Ошибка при получении сотрудников: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.get("/{employee_id}", response_model=DefaultResponse[EmployeeResponse])
async def get_employee(
    employee_id: int,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        employee = await db_manager.employees.get_by_id(employee_id)
        if not employee:
            return DefaultResponse(error=True, message="Сотрудник не найден")
        
        employee_response = employee_to_response(employee)
        
        return DefaultResponse(error=False, message="OK", payload=employee_response)
    except Exception as e:
        logger.error(f"Ошибка при получении сотрудника: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.put("/{employee_id}", response_model=DefaultResponse[EmployeeResponse])
async def update_employee(
    employee_id: int,
    employee_update: EmployeeUpdate,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        existing_employee = await db_manager.employees.get_by_id(employee_id)
        if not existing_employee:
            return DefaultResponse(error=True, message="Сотрудник не найден")
        
        update_data = employee_update.model_dump(exclude_unset=True)
        
        if 'department_id' in update_data:
            department = await db_manager.departments.get_by_id(update_data['department_id'])
            if not department:
                return DefaultResponse(error=True, message="Указанный отдел не существует")
        
        if 'role_id' in update_data:
            role = await db_manager.roles.get_by_id(update_data['role_id'])
            if not role:
                return DefaultResponse(error=True, message="Указанная должность не существует")
        
        if 'username' in update_data or 'date_of_birth' in update_data:
            username = update_data.get('username', existing_employee.username)
            date_of_birth = update_data.get('date_of_birth', existing_employee.date_of_birth)
            
            exists = await db_manager.employees.check_employee_exists(
                username, 
                date_of_birth, 
                exclude_id=employee_id
            )
            if exists:
                return DefaultResponse(
                    error=True, 
                    message="Сотрудник с таким ФИО и датой рождения уже существует"
                )
        
        success = await db_manager.employees.update(employee_id, update_data)
        if not success:
            return DefaultResponse(error=True, message="Сотрудник не найден или данные не изменились")
        
        updated_employee = await db_manager.employees.get_by_id(employee_id)
        employee_response = employee_to_response(updated_employee)
        
        return DefaultResponse(error=False, message="Сотрудник успешно обновлен", payload=employee_response)
    except Exception as e:
        logger.error(f"Ошибка при обновлении сотрудника: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.delete("/{employee_id}", response_model=DefaultResponse)
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        success = await db_manager.employees.delete(employee_id)
        if not success:
            return DefaultResponse(error=True, message="Сотрудник не найден")
        return DefaultResponse(error=False, message="Сотрудник успешно удален")
    except Exception as e:
        logger.error(f"Ошибка при удалении сотрудника: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()