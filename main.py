import os
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
Base = declarative_base()
engine = create_engine("sqlite:///./medical.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    specialty = Column(String)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    time = Column(DateTime)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username: raise HTTPException(401)
    except JWTError: raise HTTPException(401)
    user = db.query(User).filter(User.username == username).first()
    if not user: raise HTTPException(401)
    return user

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Failed")
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode({"sub": user.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/users/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    user = User(username=username, hashed_password=pwd_context.hash(password))
    db.add(user); db.commit(); return {"ok": True}

@app.post("/doctors/")
def create_doctor(name: str, spec: str, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    doc = Doctor(name=name, specialty=spec)
    db.add(doc); db.commit(); db.refresh(doc); return doc

@app.get("/doctors/")
def list_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()

@app.post("/appointments/")
def create_app(doc_id: int, pat_id: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    if not db.query(Doctor).get(doc_id) or not db.query(Patient).get(pat_id):
        raise HTTPException(400, "No doctor/patient")
    new = Appointment(doctor_id=doc_id, patient_id=pat_id, time=datetime.now())
    db.add(new); db.commit(); return new