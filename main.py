from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime

DB_URL = "sqlite:///./medical.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

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

Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.post("/appointments/")
def create_appointment(doc_id: int, pat_id: int, time: datetime, db: Session = Depends(get_db)):
    busy = db.query(Appointment).filter(Appointment.doctor_id == doc_id, Appointment.time == time).first()
    if busy:
        raise HTTPException(status_code=400, detail="Doctor is busy")
    new_app = Appointment(doctor_id=doc_id, patient_id=pat_id, time=time)
    db.add(new_app)
    db.commit()
    return {"status": "created"}
