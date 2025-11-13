from fastapi import APIRouter, Depends, Query
from typing import Optional, List
import logging

from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.db.database import db_manager
from app.core.dependencies import require_admin, require_employee_or_admin
from app.models.user import User
from app.core.config import DefaultResponse
from app.core.converters import role_to_response, roles_to_response_list

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=DefaultResponse[RoleResponse])
async def create_role(
    role: RoleCreate,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        role_data = role.model_dump()

        existing_role = await db_manager.roles.get_by_name(role_data['role_name'])
        if existing_role:
            return DefaultResponse(
                error=True, 
                message="Роль с таким названием уже существует"
            )
        
        new_role = await db_manager.roles.create(role_data)
        
        if not new_role:
            return DefaultResponse(error=True, message="Не удалось создать роль")
        
        role_response = role_to_response(new_role)
        
        return DefaultResponse(
            error=False, 
            message="Роль успешно создана", 
            payload=role_response
        )
    except Exception as e:
        logger.error(f"Ошибка при создании роли: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.get("/", response_model=DefaultResponse[List[RoleResponse]])
async def get_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    current_user: User = Depends(require_employee_or_admin)
):
    await db_manager.create_connection()
    try:
        all_roles = await db_manager.roles.get_all(skip=0, limit=1000)
        
        if search:
            filtered_roles = [
                role for role in all_roles 
                if search.lower() in role.role_name.lower() or 
                   (role.description and search.lower() in role.description.lower())
            ]
        else:
            filtered_roles = all_roles
        
        paginated_roles = filtered_roles[skip:skip + limit]
        
        roles_response = roles_to_response_list(paginated_roles)
        
        return DefaultResponse(
            error=False, 
            message="OK", 
            payload=roles_response
        )
    except Exception as e:
        logger.error(f"Ошибка при получении ролей: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.get("/{role_id}", response_model=DefaultResponse[RoleResponse])
async def get_role(
    role_id: int,
    current_user: User = Depends(require_employee_or_admin)
):
    await db_manager.create_connection()
    try:
        role = await db_manager.roles.get_by_id(role_id)
        if not role:
            return DefaultResponse(error=True, message="Роль не найдена")
        
        role_response = role_to_response(role)
        
        return DefaultResponse(
            error=False, 
            message="OK", 
            payload=role_response
        )
    except Exception as e:
        logger.error(f"Ошибка при получении роли: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.put("/{role_id}", response_model=DefaultResponse[RoleResponse])
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        existing_role = await db_manager.roles.get_by_id(role_id)
        if not existing_role:
            return DefaultResponse(error=True, message="Роль не найдена")
        
        update_data = role_update.model_dump(exclude_unset=True)
        
        if 'role_name' in update_data:
            role_with_same_name = await db_manager.roles.get_by_name(update_data['role_name'])
            if role_with_same_name and role_with_same_name.id != role_id:
                return DefaultResponse(
                    error=True, 
                    message="Роль с таким названием уже существует"
                )
        
        success = await db_manager.roles.update(role_id, update_data)
        
        if not success:
            return DefaultResponse(
                error=True, 
                message="Роль не найдена или данные не изменились"
            )
        
        updated_role = await db_manager.roles.get_by_id(role_id)
        role_response = role_to_response(updated_role)
        
        return DefaultResponse(
            error=False, 
            message="Роль успешно обновлена", 
            payload=role_response
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении роли: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.delete("/{role_id}", response_model=DefaultResponse)
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_admin)
):
    await db_manager.create_connection()
    try:
        role = await db_manager.roles.get_by_id(role_id)
        if not role:
            return DefaultResponse(error=True, message="Роль не найдена")
        
        has_employees = await db_manager.roles.check_has_employees(role_id)
        if has_employees:
            return DefaultResponse(
                error=True, 
                message="Невозможно удалить роль: есть сотрудники с этой ролью"
            )
        
        success = await db_manager.roles.delete(role_id)
        
        if not success:
            return DefaultResponse(error=True, message="Роль не найдена")
        
        return DefaultResponse(error=False, message="Роль успешно удалена")
    except Exception as e:
        logger.error(f"Ошибка при удалении роли: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()