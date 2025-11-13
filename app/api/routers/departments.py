from fastapi import APIRouter, Depends
from typing import List
import logging

from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.db.database import db_manager
from app.models.user import User
from app.core.dependencies import require_admin, require_employee_or_admin
from app.core.config import DefaultResponse
from app.core.converters import department_to_response, departments_to_response_list

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=DefaultResponse[DepartmentResponse])
async def create_department(
    department: DepartmentCreate,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        department_data = department.model_dump()
        
        if department_data.get('manager_id'):
            manager = await db_manager.employees.get_by_id(department_data['manager_id'])
            if not manager:
                return DefaultResponse(error=True, message="Указанный менеджер не существует")
        
        new_department = await db_manager.departments.create(department_data)

        if not new_department:
            return DefaultResponse(error=True, message="Не удалось создать отдел")
        
        department_response = department_to_response(new_department)
        
        return DefaultResponse(error=False, message="Отдел успешно создан", payload=department_response)

    except Exception as e:
        logger.error(f"Ошибка при создании отдела: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.get("/", response_model=DefaultResponse[List[DepartmentResponse]])
async def get_departments(
    current_user: User = Depends(require_employee_or_admin)
):
    await db_manager.create_connection()
    try:
        departments = await db_manager.departments.get_all()
        
        departments_response = departments_to_response_list(departments)
        
        return DefaultResponse(error=False, message="OK", payload=departments_response)
    except Exception as e:
        logger.error(f"Ошибка при получении всех отделов: {e}")
        return DefaultResponse(error=True, message="Не удалось получить все отделы")
    finally:
        await db_manager.close_connection()

@router.get("/{department_id}", response_model=DefaultResponse[DepartmentResponse])
async def get_department(
    department_id: int,
    current_user: User = Depends(require_employee_or_admin)
):
    await db_manager.create_connection()
    try:
        department = await db_manager.departments.get_by_id(department_id)
        if not department:
            return DefaultResponse(error=True, message="Отдел не найден")
        
        department_response = department_to_response(department)
        
        return DefaultResponse(error=False, message="OK", payload=department_response)
    except Exception as e:
        logger.error(f"Ошибка при получении отдела: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.put("/{department_id}", response_model=DefaultResponse[DepartmentResponse])
async def update_department(
    department_id: int, 
    department_update: DepartmentUpdate,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        existing_department = await db_manager.departments.get_by_id(department_id)
        if not existing_department:
            return DefaultResponse(error=True, message="Отдел не найден")
        
        update_data = department_update.model_dump(exclude_unset=True)
        
        if update_data.get('manager_id'):
            manager = await db_manager.employees.get_by_id(update_data['manager_id'])
            if not manager:
                return DefaultResponse(error=True, message="Указанный менеджер не существует")
        
        success = await db_manager.departments.update(department_id, update_data)
        if not success:
            return DefaultResponse(error=True, message="Отдел не найден или данные не изменились")
        
        updated_department = await db_manager.departments.get_by_id(department_id)
        department_response = department_to_response(updated_department)
        
        return DefaultResponse(error=False, message="Отдел успешно обновлен", payload=department_response)
    except Exception as e:
        logger.error(f"Ошибка при обновлении отдела: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.delete("/{department_id}", response_model=DefaultResponse)
async def delete_department(
    department_id: int,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        department = await db_manager.departments.get_by_id(department_id)
        if not department:
            return DefaultResponse(error=True, message="Отдел не найден")
        
        has_employees = await db_manager.departments.check_has_employees(department_id)
        if has_employees:
            return DefaultResponse(
                error=True, 
                message="Невозможно удалить отдел: в нем есть сотрудники"
            )

        success = await db_manager.departments.delete(department_id)
        if not success:
            return DefaultResponse(error=True, message="Отдел не найден")
        
        return DefaultResponse(error=False, message="Отдел успешно удален")
    except Exception as e:
        logger.error(f"Ошибка при удалении отдела: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()