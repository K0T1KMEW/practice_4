import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, update, delete, text
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any

from app.models.base import Base
from app.models.models import Employees, Departments, Skills
from app.models.user import User
from app.logger_config import setup_logger

logger = setup_logger(__name__)
load_dotenv()

class EmployeeDatabaseManager:
    def __init__(self):
        self.engine = None
        self.async_session = None
        self.session = None
        self._initialized = False

    async def check_database_exists(self) -> bool:
        try:
            database_name = os.getenv('DB_NAME', 'employee_db')
            test_url = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{database_name}"
            
            test_engine = create_async_engine(test_url, echo=False)
            async with test_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await test_engine.dispose()
            return True
        except Exception as e:
            logger.error(f"к базе подключиться ни-ни: {e}")
            return False

    async def check_tables_exist(self) -> bool:
        if not self.engine:
            return False
            
        try:
            async with self.engine.connect() as conn:
                tables_to_check = ['users', 'employees', 'departments', 'skills', 'employee_skill']
                
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
                        logger.warning(f"таблица {table_name} не-не")
                        return False
                
                logger.info("таблицы оке")
                return True
        except Exception as e:
            logger.error(f"таблицы не оке: {e}")
            return False

    async def initialize_database(self):
        if self._initialized:
            return True
            
        try:
            if not await self.check_database_exists():
                logger.error("к базе ни-ни")
                return False
            
            database_name = os.getenv('DB_NAME', 'employee_db')
            database_url = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{database_name}"
            
            self.engine = create_async_engine(database_url, echo=False)
            self.async_session = async_sessionmaker(
                self.engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            tables_exist = await self.check_tables_exist()
            
            if not tables_exist:
                logger.info("создане таблц...")
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("таблы созднаы")
            else:
                logger.info("база не-не")
            
            self._initialized = True
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка инициализации базы данных сотрудников: {e}")
            return False

    # async def initialize_database(self):
    #     if self._initialized:
    #         return True
            
    #     try:
    #         database_name = os.getenv('DB_NAME', 'employee_db')
    #         database_url = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{database_name}"
            
    #         self.engine = create_async_engine(database_url, echo=False)
    #         self.async_session = async_sessionmaker(
    #             self.engine, 
    #             class_=AsyncSession, 
    #             expire_on_commit=False
    #         )
            
    #         async with self.engine.begin() as conn:
    #             await conn.run_sync(Base.metadata.create_all)
            
    #         logger.info("База данных сотрудников и таблицы инициализированы")
    #         self._initialized = True
    #         return True
            
    #     except SQLAlchemyError as e:
    #         logger.error(f"Ошибка инициализации базы данных сотрудников: {e}")
    #         return False

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
            logger.info("Сессия с базой данных сотрудников создана успешно")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка подключения к базе сотрудников: {e}")
            return False

    async def close_connection(self):
        if self.session:
            await self.session.close()
            logger.info("Сессия с базой данных сотрудников закрыта")
        
        if self.engine:
            await self.engine.dispose()

    async def get_employee_by_id(self, employee_id: int) -> Optional[Employees]:
        if not self.session:
            return None
            
        try:
            result = await self.session.execute(
                select(Employees).where(Employees.id == employee_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка получения сотрудника по ID: {e}")
            return None

    async def get_all_employees(
        self, 
        skip: int = 0, 
        limit: int = 100,
        department: Optional[str] = None,
        status: Optional[str] = None,
        job_title: Optional[str] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Employees]:
        if not self.session:
            return []
            
        try:
            query = select(Employees)
            
            if department:
                query = query.where(Employees.department == department)
            if status:
                query = query.where(Employees.status == status)
            if job_title:
                query = query.where(Employees.job_title == job_title)
            if min_salary is not None:
                query = query.where(Employees.salary >= min_salary)
            if max_salary is not None:
                query = query.where(Employees.salary <= max_salary)
            if search:
                query = query.where(Employees.username.ilike(f"%{search}%"))
            
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка получения списка сотрудников: {e}")
            return []

    async def create_employee(self, employee_data: Dict[str, Any]) -> Optional[Employees]:
        if not self.session:
            return None
            
        try:
            employee = Employees(**employee_data)
            self.session.add(employee)
            await self.session.commit()
            await self.session.refresh(employee)
            logger.info(f"Сотрудник {employee.username} успешно создан")
            return employee
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка создания сотрудника: {e}")
            await self.session.rollback()
            return None

    async def update_employee(self, employee_id: int, update_data: Dict[str, Any]) -> bool:
        if not self.session:
            return False
            
        try:
            update_data.pop('id', None)
            
            result = await self.session.execute(
                update(Employees)
                .where(Employees.id == employee_id)
                .values(**update_data)
            )
            await self.session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Сотрудник с ID {employee_id} успешно обновлен")
                return True
            return False
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка обновления сотрудника: {e}")
            await self.session.rollback()
            return False

    async def delete_employee(self, employee_id: int) -> bool:
        if not self.session:
            return False
            
        try:
            result = await self.session.execute(
                delete(Employees).where(Employees.id == employee_id)
            )
            await self.session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Сотрудник с ID {employee_id} успешно удален")
                return True
            return False
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка удаления сотрудника: {e}")
            await self.session.rollback()
            return False

    async def get_all_departments(self) -> List[Departments]:
        if not self.session:
            return []
            
        try:
            result = await self.session.execute(select(Departments))
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка получения списка отделов: {e}")
            return []

    async def get_department_by_id(self, department_id: int) -> Optional[Departments]:
        if not self.session:
            return None
            
        try:
            result = await self.session.execute(
                select(Departments).where(Departments.id == department_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка получения отдела по ID: {e}")
            return None

    async def create_department(self, department_data: Dict[str, Any]) -> Optional[Departments]:
        if not self.session:
            return None
            
        try:
            department = Departments(
                department_name=department_data['department_name'],
                manager_id=department_data.get('manager_id')
            )
            self.session.add(department)
            await self.session.commit()
            await self.session.refresh(department)
            logger.info(f"Отдел {department.department_name} успешно создан")
            return department
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка создания отдела: {e}")
            await self.session.rollback()
            return None

    async def update_department(self, department_id: int, update_data: Dict[str, Any]) -> bool:
        if not self.session:
            return False
            
        try:
            result = await self.session.execute(
                update(Departments)
                .where(Departments.id == department_id)
                .values(**update_data)
            )
            await self.session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Отдел с ID {department_id} успешно обновлен")
                return True
            return False
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка обновления отдела: {e}")
            await self.session.rollback()
            return False

    async def delete_department(self, department_id: int) -> bool:
        if not self.session:
            return False
            
        try:
            employees_count = await self.session.execute(
                select(Employees).where(Employees.department_id == department_id)
            )
            if employees_count.scalars().first():
                logger.error("Невозможно удалить отдел: в нем есть сотрудники")
                return False
            
            result = await self.session.execute(
                delete(Departments).where(Departments.id == department_id)
            )
            await self.session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Отдел с ID {department_id} успешно удален")
                return True
            return False
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка удаления отдела: {e}")
            await self.session.rollback()
            return False

    # async def get_all_skills(self) -> List[Skills]:
    #     if not self.session:
    #         return []
            
    #     try:
    #         result = await self.session.execute(select(Skills))
    #         return result.scalars().all()
    #     except SQLAlchemyError as e:
    #         logger.error(f"Ошибка получения списка навыков: {e}")
    #         return []

    # async def add_skill_to_employee(self, employee_id: int, skill_id: int) -> bool:
    #     if not self.session:
    #         return False
            
    #     try:
    #         employee = await self.get_employee_by_id(employee_id)
    #         skill = await self.session.execute(
    #             select(Skills).where(Skills.id == skill_id)
    #         )
    #         skill = skill.scalar_one_or_none()
            
    #         if employee and skill and skill not in employee.skills:
    #             employee.skills.append(skill)
    #             await self.session.commit()
    #             logger.info(f"Навык добавлен сотруднику {employee_id}")
    #             return True
    #         return False
            
    #     except SQLAlchemyError as e:
    #         logger.error(f"Ошибка добавления навыка сотруднику: {e}")
    #         await self.session.rollback()
    #         return False

    # async def remove_skill_from_employee(self, employee_id: int, skill_id: int) -> bool:
    #     if not self.session:
    #         return False
            
    #     try:
    #         employee = await self.get_employee_by_id(employee_id)
    #         skill = await self.session.execute(
    #             select(Skills).where(Skills.id == skill_id)
    #         )
    #         skill = skill.scalar_one_or_none()
            
    #         if employee and skill and skill in employee.skills:
    #             employee.skills.remove(skill)
    #             await self.session.commit()
    #             logger.info(f"Навык удален у сотрудника {employee_id}")
    #             return True
    #         return False
            
    #     except SQLAlchemyError as e:
    #         logger.error(f"Ошибка удаления навыка у сотрудника: {e}")
    #         await self.session.rollback()
    #         return False
        

    async def get_user_by_username(self, username: str) -> Optional[User]:
        if not self.session:
            return None
            
        try:
            result = await self.session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"ошибка получения юзера по айди: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        if not self.session:
            return None
            
        try:
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"ошибка получения юзера по почте: {e}")
            return None

    async def create_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        if not self.session:
            return None
            
        try:
            user = User(**user_data)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"юзер {user.username} успешно создан")
            return user
        except SQLAlchemyError as e:
            logger.error(f"ошибка создания юзера: {e}")
            await self.session.rollback()
            return None

db_manager = EmployeeDatabaseManager()