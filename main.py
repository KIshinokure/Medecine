from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timedelta
import jose.jwt as jwt

# Конфигурация
SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"
Base = declarative_base()
engine = create_engine("sqlite:///./medical.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Модели (4 сущности: Врачи, Пациенты, Записи, Медкарты)
class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    specialty = Column(String)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    policy = Column(String, unique=True)

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    time = Column(DateTime)

class MedicalRecord(Base):
    __tablename__ = "records"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    diagnosis = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Инструменты JWT
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return {"access_token": create_access_token({"sub": form_data.username}), "token_type": "bearer"}

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# CRUD с защитой (Задание 1)
@app.post("/appointments/")
def create_app(doc_id: int, pat_id: int, time: datetime, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    busy = db.query(Appointment).filter(Appointment.doctor_id == doc_id, Appointment.time == time).first()
    if busy: raise HTTPException(400, "Doctor busy")
    new = Appointment(doctor_id=doc_id, patient_id=pat_id, time=time)
    db.add(new); db.commit()
    return {"status": "success"}

@app.get("/analytics/") # Мини-аналитика
def get_analytics(db: Session = Depends(get_db)):
    count = db.query(Appointment).count()
    return {"total_appointments": count}
