from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from .base import Base

#Base = declarative_base()

employee_skill_association = Table(
    'employee_skill',
    Base.metadata,
    Column('employee_id', Integer, ForeignKey('employees.id')),
    Column('skill_id', Integer, ForeignKey('skills.id'))
)

class Employees(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    date_of_birth = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    department = Column(String(20), nullable=False)
    job_title = Column(String(20), nullable=False)
    bet = Column(Integer, nullable=False)
    salary = Column(Integer, nullable=False)
    date_of_admission = Column(String(20), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'))
    
    department_rel = relationship("Departments", back_populates="employees", foreign_keys=[department_id])
    skills = relationship("Skills", secondary=employee_skill_association, back_populates="employees")

class Departments(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(255), nullable=False, unique=True)
    manager_id = Column(Integer, ForeignKey('employees.id'))
    
    employees = relationship("Employees", back_populates="department_rel", foreign_keys="Employees.department_id")
    manager = relationship("Employees", foreign_keys=[manager_id])

class Skills(Base):
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(20), nullable=False, unique=True)
    
    employees = relationship("Employees", secondary=employee_skill_association, back_populates="skills")