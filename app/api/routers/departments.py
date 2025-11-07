from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.db.database import db_manager
from app.models.user import User
from app.core.dependencies import require_admin, require_employee_or_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=DepartmentResponse)
async def create_department(
    department: DepartmentCreate,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        department_data = department.model_dump()
        new_department = await db_manager.create_department(department_data)

        if not new_department:
            raise HTTPException(status_code=400, detail="Не удалось создать отдел")
        
        return new_department

    except Exception as e:
        logger.error(f"Ошибка при создании отдела: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    current_user: User = Depends(require_employee_or_admin)
):
    await db_manager.create_connection()
    try:
        departments = await db_manager.get_all_departments()
        return departments
    except Exception as e:
        logger.error(f"Ошибка при получении всех отделов: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить все отделы")
    finally:
        await db_manager.close_connection()

@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(department_id: int):
    await db_manager.create_connection()
    try:
        department = await db_manager.get_department_by_id(department_id)
        if not department:
            raise HTTPException(status_code=404, detail="Отдел не найден")
        return department
    except Exception as e:
        logger.error(f"Ошибка при получении отдела: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(department_id: int, department_update: DepartmentUpdate):
    await db_manager.create_connection()
    try:
        update_data = department_update.model_dump(exclude_unset=True)
        
        success = await db_manager.update_department(department_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Отдел не найден или данные не изменились")
        
        updated_department = await db_manager.get_department_by_id(department_id)
        return updated_department
    except Exception as e:
        logger.error(f"Ошибка при обновлении отдела: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.delete("/{department_id}")
async def delete_department(department_id: int):
    await db_manager.create_connection()
    try:
        success = await db_manager.delete_department(department_id)
        if not success:
            raise HTTPException(status_code=404, detail="Отдел не найден")
        return {"message": "Отдел успешно удален"}
    except Exception as e:
        logger.error(f"Ошибка при удалении отдела: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()