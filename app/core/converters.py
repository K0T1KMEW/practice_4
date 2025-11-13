from typing import List
from app.schemas.employee import EmployeeResponse
from app.schemas.department import DepartmentResponse
from app.schemas.role import RoleResponse
from app.models.models import Employees, Departments
from app.models.role import Role

def employee_to_response(employee: Employees) -> EmployeeResponse:
    return EmployeeResponse(
        id=employee.id,
        username=employee.username,
        date_of_birth=employee.date_of_birth,
        department_id=employee.department_id,
        role_id=employee.role_id,
        salary=employee.salary,
        bet=employee.bet,
        status=employee.status,
        date_of_admission=employee.date_of_admission,
        photo=employee.photo,
        department_name=employee.department.department_name if employee.department else None,
        role_name=employee.role.role_name if employee.role else None
    )

def employees_to_response_list(employees: List[Employees]) -> List[EmployeeResponse]:
    return [employee_to_response(emp) for emp in employees]

def department_to_response(department: Departments) -> DepartmentResponse:
    manager_name = None
    if department.manager:
        manager_name = department.manager.username
    
    return DepartmentResponse(
        id=department.id,
        department_name=department.department_name,
        manager_id=department.manager_id,
        manager_name=manager_name
    )

def departments_to_response_list(departments: List[Departments]) -> List[DepartmentResponse]:
    return [department_to_response(dept) for dept in departments]

def role_to_response(role: Role) -> RoleResponse:
    return RoleResponse(
        id=role.id,
        role_name=role.role_name,
        description=role.description
    )

def roles_to_response_list(roles: List[Role]) -> List[RoleResponse]:
    return [role_to_response(role) for role in roles]