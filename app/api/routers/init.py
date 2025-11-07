from .auth import router as auth_router
from .employees import router as employees_router
from .departments import router as departments_router

__all__ = ['auth_router', 'employees_router', 'departments_router']