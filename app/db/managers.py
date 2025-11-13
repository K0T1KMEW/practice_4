from sqlalchemy import select
from typing import List, Optional, Dict, Any
from app.models.models import Employees, Departments
from app.models.user import User
from app.models.role import Role
from app.db.base_manager import BaseManager
from app.logger.logger_config import setup_logger
logger = setup_logger(__name__)

class EmployeeManager(BaseManager[Employees]):
    def __init__(self, session):
        super().__init__(session, Employees)

    async def get_all_employees(
        self, 
        skip: int = 0, 
        limit: int = 100,
        department_id: Optional[int] = None,
        status: Optional[str] = None,
        role_id: Optional[int] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Employees]:
        try:
            query = select(Employees)
            
            if department_id:
                query = query.where(Employees.department_id == department_id)
            if status:
                query = query.where(Employees.status == status)
            if role_id:
                query = query.where(Employees.role_id == role_id)
            if min_salary is not None:
                query = query.where(Employees.salary >= min_salary)
            if max_salary is not None:
                query = query.where(Employees.salary <= max_salary)
            if search:
                query = query.where(Employees.username.ilike(f"%{search}%"))
            
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка получения списка сотрудников: {e}")
            return []

    async def check_employee_exists(self, username: str, date_of_birth: str, exclude_id: Optional[int] = None) -> bool:
        try:
            query = select(Employees).where(
                Employees.username == username,
                Employees.date_of_birth == date_of_birth
            )
            
            if exclude_id:
                query = query.where(Employees.id != exclude_id)
                
            result = await self.session.execute(query)
            employee = result.scalar_one_or_none()
            return employee is not None
        except Exception as e:
            logger.error(f"Ошибка проверки существования сотрудника: {e}")
            return False

class DepartmentManager(BaseManager[Departments]):
    def __init__(self, session):
        super().__init__(session, Departments)

    async def check_has_employees(self, department_id: int) -> bool:
        try:
            result = await self.session.execute(
                select(Employees).where(Employees.department_id == department_id)
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки сотрудников в отделе: {e}")
            return False

class RoleManager(BaseManager[Role]):
    def __init__(self, session):
        super().__init__(session, Role)

    async def get_by_name(self, role_name: str) -> Optional[Role]:
        try:
            result = await self.session.execute(
                select(Role).where(Role.role_name == role_name)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения роли по имени: {e}")
            return None

    async def check_has_employees(self, role_id: int) -> bool:
        try:
            result = await self.session.execute(
                select(Employees).where(Employees.role_id == role_id)
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки сотрудников с ролью: {e}")
            return False

class UserManager(BaseManager[User]):
    def __init__(self, session):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по имени: {e}")
            return None

    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по email: {e}")
            return None