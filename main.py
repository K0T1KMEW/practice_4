from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
import os
import uuid

from app.api.routers import auth, employees, departments
from app.db.database import db_manager
from app.core.security import verify_password, create_access_token
from app.logger.logger_config import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("стартуем...")
    if await db_manager.initialize_database():
        logger.info("база ок")
    else:
        logger.error("база не ок")
    yield
    logger.info("бай-бай")

app = FastAPI(lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")

os.makedirs(UPLOADS_DIR, exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(employees.router, prefix="/api/employees", tags=["employees"])
app.include_router(departments.router, prefix="/api/departments", tags=["departments"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    await db_manager.create_connection()
    try:
        user = await db_manager.get_user_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            return templates.TemplateResponse(
                "index.html", 
                {"request": request, "error": "Неверный логин или пароль"}
            )
        
        access_token = create_access_token(data={"sub": user.username, "role": user.role})
        
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="access_token", 
            value=f"Bearer {access_token}",
            httponly=False,
            max_age=1800
        )
        return response
    except Exception as e:
        logger.error(f"Login error: {e}")
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "error": "Ошибка входа"}
        )
    finally:
        await db_manager.close_connection()

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

@app.get("/add-employee", response_class=HTMLResponse)
async def add_employee_page(request: Request):
    token = request.cookies.get("access_token", "").replace("Bearer ", "")
    if not token:
        return RedirectResponse(url="/")
    
    return templates.TemplateResponse("add_employee.html", {"request": request})

@app.post("/add-employee")
async def add_employee(
    request: Request,
    username: str = Form(...),
    date_of_birth: str = Form(...),
    department: str = Form(...),
    job_title: str = Form(...),
    salary: int = Form(...),
    bet: int = Form(...),
    photo: UploadFile = File(None)
):
    token = request.cookies.get("access_token", "").replace("Bearer ", "")
    if not token:
        return RedirectResponse(url="/")
    
    photo_url = None
    if photo and photo.filename:
        file_extension = photo.filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOADS_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)
        
        photo_url = f"/static/uploads/{filename}"
    
    employee_data = {
        "username": username,
        "date_of_birth": date_of_birth,
        "department": department,
        "job_title": job_title,
        "salary": salary,
        "bet": bet,
        "status": "active",
        "date_of_admission": "2024-01-01",
        "photo": photo_url
    }
    
    await db_manager.create_connection()
    try:
        new_employee = await db_manager.create_employee(employee_data)
        if new_employee:
            return RedirectResponse(url="/", status_code=302)
        else:
            return templates.TemplateResponse(
                "add_employee.html", 
                {"request": request, "error": "Ошибка при создании сотрудника"}
            )
    except Exception as e:
        logger.error(f"Error creating employee: {e}")
        return templates.TemplateResponse(
            "add_employee.html", 
            {"request": request, "error": f"Ошибка: {str(e)}"}
        )
    finally:
        await db_manager.close_connection()

@app.get("/edit-employee/{employee_id}", response_class=HTMLResponse)
async def edit_employee_page(request: Request, employee_id: int):
    token = request.cookies.get("access_token", "").replace("Bearer ", "")
    if not token:
        return RedirectResponse(url="/")
    
    await db_manager.create_connection()
    try:
        employee = await db_manager.get_employee_by_id(employee_id)
        if not employee:
            return RedirectResponse(url="/")
        return templates.TemplateResponse("edit_employee.html", {"request": request, "employee": employee})
    except Exception as e:
        logger.error(f"Error getting employee {employee_id}: {e}")
        return RedirectResponse(url="/")
    finally:
        await db_manager.close_connection()

@app.post("/edit-employee/{employee_id}")
async def edit_employee(
    request: Request,
    employee_id: int,
    username: str = Form(...),
    date_of_birth: str = Form(...),
    department: str = Form(...),
    job_title: str = Form(...),
    salary: int = Form(...),
    bet: int = Form(...),
    status: str = Form(...),
    photo: UploadFile = File(None)
):
    token = request.cookies.get("access_token", "").replace("Bearer ", "")
    if not token:
        return RedirectResponse(url="/")
    
    photo_url = None
    if photo and photo.filename:
        file_extension = photo.filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOADS_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)
        
        photo_url = f"/static/uploads/{filename}"
    
    update_data = {
        "username": username,
        "date_of_birth": date_of_birth,
        "department": department,
        "job_title": job_title,
        "salary": salary,
        "bet": bet,
        "status": status
    }
    
    if photo_url:
        update_data["photo"] = photo_url
    
    await db_manager.create_connection()
    try:
        success = await db_manager.update_employee(employee_id, update_data)
        if success:
            return RedirectResponse(url="/", status_code=302)
        else:
            employee = await db_manager.get_employee_by_id(employee_id)
            return templates.TemplateResponse(
                "edit_employee.html", 
                {"request": request, "employee": employee, "error": "Ошибка при обновлении"}
            )
    except Exception as e:
        logger.error(f"Error updating employee {employee_id}: {e}")
        employee = await db_manager.get_employee_by_id(employee_id)
        return templates.TemplateResponse(
            "edit_employee.html", 
            {"request": request, "employee": employee, "error": f"Ошибка: {str(e)}"}
        )
    finally:
        await db_manager.close_connection()

@app.get("/employee/{employee_id}", response_class=HTMLResponse)
async def employee_page(request: Request, employee_id: int):
    await db_manager.create_connection()
    try:
        employee = await db_manager.get_employee_by_id(employee_id)
        if not employee:
            return RedirectResponse(url="/")
        return templates.TemplateResponse("employee.html", {"request": request, "employee": employee})
    except Exception as e:
        logger.error(f"Error getting employee {employee_id}: {e}")
        return RedirectResponse(url="/")
    finally:
        await db_manager.close_connection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)