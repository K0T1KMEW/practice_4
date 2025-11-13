from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any, TypeVar, Generic, Type
from sqlalchemy import select, update, delete
from app.logger.logger_config import setup_logger

T = TypeVar('T')
logger = setup_logger(__name__)

class BaseManager(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> Optional[T]:
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка получения {self.model.__name__} по ID {id}: {e}")
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        try:
            result = await self.session.execute(
                select(self.model).offset(skip).limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка получения списка {self.model.__name__}: {e}")
            return []

    async def create(self, data: Dict[str, Any]) -> Optional[T]:
        try:
            instance = self.model(**data)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            logger.info(f"{self.model.__name__} успешно создан (ID: {instance.id})")
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Ошибка создания {self.model.__name__}: {e}")
            await self.session.rollback()
            return None

    async def update(self, id: int, update_data: Dict[str, Any]) -> bool:
        try:
            update_data.pop('id', None)
            result = await self.session.execute(
                update(self.model)
                .where(self.model.id == id)
                .values(**update_data)
            )
            await self.session.commit()
            
            if result.rowcount > 0:
                logger.info(f"{self.model.__name__} с ID {id} успешно обновлен")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Ошибка обновления {self.model.__name__} с ID {id}: {e}")
            await self.session.rollback()
            return False

    async def delete(self, id: int) -> bool:
        try:
            result = await self.session.execute(
                delete(self.model).where(self.model.id == id)
            )
            await self.session.commit()
            
            if result.rowcount > 0:
                logger.info(f"{self.model.__name__} с ID {id} успешно удален")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Ошибка удаления {self.model.__name__} с ID {id}: {e}")
            await self.session.rollback()
            return False