from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
import logging

from app.schemas.auth import Token, UserRegister, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from app.db.database import db_manager
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.core.config import settings
from app.core.config import DefaultResponse

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

@router.post("/token", response_model=DefaultResponse[Token])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    await db_manager.create_connection()
    try:
        user = await db_manager.users.get_by_username(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            return DefaultResponse(
                error=True,
                message="Неверное имя пользователя или пароль"
            )
        
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role.value if hasattr(user.role, 'value') else user.role}
        )
        token_data = {"access_token": access_token, "token_type": "bearer"}
        return DefaultResponse(error=False, message="Успешная авторизация", payload=token_data)
    except Exception as e:
        logger.error(f"Ошибка авторизации: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.post("/register", response_model=DefaultResponse[Token])
async def register_user(user_data: UserRegister):
    await db_manager.create_connection()
    try:
        existing_user = await db_manager.users.get_by_username(user_data.username)
        if existing_user:
            return DefaultResponse(error=True, message="Имя пользователя уже занято")
        
        existing_email = await db_manager.users.get_by_email(user_data.email)
        if existing_email:
            return DefaultResponse(error=True, message="Email уже зарегистрирован")
        
        user_dict = user_data.model_dump()
        user_dict["role"] = "employee"
        user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
        
        new_user = await db_manager.users.create(user_dict)
        if not new_user:
            return DefaultResponse(error=True, message="Не удалось создать пользователя")
        
        access_token = create_access_token(
            data={"sub": new_user.username, "role": new_user.role}
        )
        
        token_data = {"access_token": access_token, "token_type": "bearer"}
        return DefaultResponse(error=False, message="Пользователь успешно зарегистрирован", payload=token_data)
        
    except Exception as e:
        logger.error(f"Ошибка регистрации: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.post("/register-admin", response_model=DefaultResponse[Token])
async def register_admin(
    user_data: UserRegister,
    admin_secret: str = Query(..., description="Секретный ключ для создания администратора")
):
    if admin_secret != settings.SECRET_KEY:
        return DefaultResponse(error=True, message="Неверный секретный ключ администратора")
    
    await db_manager.create_connection()
    try:
        existing_user = await db_manager.users.get_by_username(user_data.username)
        if existing_user:
            return DefaultResponse(error=True, message="Имя пользователя уже занято")
        
        existing_email = await db_manager.users.get_by_email(user_data.email)
        if existing_email:
            return DefaultResponse(error=True, message="Email уже зарегистрирован")
        
        user_dict = user_data.model_dump()
        user_dict["role"] = "admin"
        user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
        
        new_user = await db_manager.users.create(user_dict)
        if not new_user:
            return DefaultResponse(error=True, message="Не удалось создать пользователя")
        
        access_token = create_access_token(
            data={"sub": new_user.username, "role": new_user.role}
        )

        token_data = {"access_token": access_token, "token_type": "bearer"}
        return DefaultResponse(error=False, message="Администратор успешно зарегистрирован", payload=token_data)
        
    except Exception as e:
        logger.error(f"Ошибка регистрации: {e}")
        return DefaultResponse(error=True, message="Внутренняя ошибка сервера")
    finally:
        await db_manager.close_connection()

@router.get("/me", response_model=DefaultResponse[UserResponse])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    user_response = UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active
    )
    return DefaultResponse(error=False, message="OK", payload=user_response)