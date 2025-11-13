from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from .base import Base

class Employees(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="active")
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    
    bet = Column(Integer, nullable=False)
    salary = Column(Integer, nullable=False)
    date_of_admission = Column(Date, nullable=False)
    photo = Column(String(500), nullable=True)
    
    department = relationship("Departments", back_populates="employees", foreign_keys=[department_id])
    role = relationship("Role", back_populates="employees")

class Departments(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(255), nullable=False, unique=True)
    manager_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    
    employees = relationship("Employees", back_populates="department", foreign_keys="Employees.department_id")
    manager = relationship("Employees", foreign_keys=[manager_id], remote_side="Employees.id", post_update=True)