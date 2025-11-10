from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
import logging
from pydantic_settings import BaseSettings

from app.schemas.auth import Token, UserRegister, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from app.db.database import db_manager
from app.models.user import User
from app.core.dependencies import get_current_active_user

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    secret_key: str
    
    class Config:
        env_file = ".env"

settings = Settings()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    await db_manager.create_connection()
    try:
        user = await db_manager.get_user_by_username(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role.value if hasattr(user.role, 'value') else user.role}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    finally:
        await db_manager.close_connection()

@router.post("/register", response_model=Token)
async def register_user(user_data: UserRegister):
    await db_manager.create_connection()
    try:
        existing_user = await db_manager.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        existing_email = await db_manager.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user_dict = user_data.model_dump()
        user_dict["role"] = "employee"
        user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
        
        new_user = await db_manager.create_user(user_dict)
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create user"
            )
        
        access_token = create_access_token(
            data={"sub": new_user.username, "role": new_user.role}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    finally:
        await db_manager.close_connection()

@router.post("/register-admin", response_model=Token)
async def register_admin(
    user_data: UserRegister,
    admin_secret: str = Query(..., description="Секретный ключ для создания администратора")
):
    if admin_secret != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin secret key"
        )
    
    await db_manager.create_connection()
    try:
        existing_user = await db_manager.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        existing_email = await db_manager.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user_dict = user_data.model_dump()
        user_dict["role"] = "admin"
        user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
        
        new_user = await db_manager.create_user(user_dict)
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create user"
            )
        
        access_token = create_access_token(
            data={"sub": new_user.username, "role": new_user.role}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    finally:
        await db_manager.close_connection()

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active
    )