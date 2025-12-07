from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal, engine
from models import Base, Data

class DataIn(BaseModel):
    name: str
    value: str

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# curl -X POST http://127.0.0.1:8000/submit ^
#   -H "Content-Type: application/json" ^
#   -d "{\"name\":\"test\",\"value\":\"123\"}"

@app.post("/submit")
def submit_data(payload: DataIn, db: Session = Depends(get_db)):
    record = Data(name=payload.name, value=payload.value)
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"status": "saved", "id": record.id}

@app.get("/data")
def get_all_data(db: Session = Depends(get_db)):
    return db.query(Data).all()
