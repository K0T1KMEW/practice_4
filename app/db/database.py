import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from typing import List, Optional, Dict, Any

from app.models.base import Base
from app.db.managers import EmployeeManager, DepartmentManager, RoleManager, UserManager
from app.logger.logger_config import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.async_session = None
        self.session = None
        self._initialized = False
        
        self.employees = None
        self.departments = None
        self.roles = None
        self.users = None

    async def check_database_exists(self) -> bool:
        try:
            test_url = settings.DATABASE_URL
            test_engine = create_async_engine(test_url, echo=False)
            async with test_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await test_engine.dispose()
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            return False

    async def check_tables_exist(self) -> bool:
        if not self.engine:
            return False
            
        try:
            async with self.engine.connect() as conn:
                tables_to_check = ['users', 'employees', 'departments', 'roles']
                
                for table_name in tables_to_check:
                    result = await conn.execute(
                        text("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = :table_name
                            )
                        """), {'table_name': table_name}
                    )
                    exists = result.scalar()
                    if not exists:
                        logger.warning(f"Таблица {table_name} не найдена")
                        return False
                
                logger.info("Все необходимые таблицы существуют")
                return True
        except Exception as e:
            logger.error(f"Ошибка проверки таблиц: {e}")
            return False

    async def initialize_database(self):
        if self._initialized:
            return True
            
        try:
            if not await self.check_database_exists():
                logger.error("Не удалось подключиться к базе данных")
                return False
            
            database_url = settings.DATABASE_URL
            
            self.engine = create_async_engine(database_url, echo=False)
            self.async_session = async_sessionmaker(
                self.engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            tables_exist = await self.check_tables_exist()
            
            if not tables_exist:
                logger.info("Создание таблиц...")
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("Таблицы успешно созданы")
            else:
                logger.info("Таблицы уже существуют")
            
            self._initialized = True
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            return False

    async def create_connection(self):
        try:
            if not self._initialized:
                success = await self.initialize_database()
                if not success:
                    logger.error("Не удалось инициализировать базу данных")
                    return False
            
            if not self.async_session:
                logger.error("Сессия не инициализирована")
                return False
            
            self.session = self.async_session()
            
            self.employees = EmployeeManager(self.session)
            self.departments = DepartmentManager(self.session)
            self.roles = RoleManager(self.session)
            self.users = UserManager(self.session)
            
            logger.info("Сессия базы данных создана успешно")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка создания сессии базы данных: {e}")
            return False

    async def close_connection(self):
        if self.session:
            await self.session.close()
            logger.info("Сессия базы данных закрыта")
        
        if self.engine:
            await self.engine.dispose()

db_manager = DatabaseManager()