from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.api.routers import auth, employees, departments
from app.core.config import settings
from app.db.database import db_manager
from app.core.security import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    if await db_manager.initialize_database():
        print("all rigth")
    else:
        print("boba")
    yield

app = FastAPI(
    title="Employee Management System", 
    lifespan=lifespan
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(employees.router, prefix="/employees", tags=["employees"])
app.include_router(departments.router, prefix="/departments", tags=["departments"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)