from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, database
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware


models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="StayAwake Backend - Sensores")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # Puedes restringir a ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"ok": True, "service": "StayAwake Backend - Sensores"}

@app.post("/sensores/", response_model=schemas.SensorDataResponse)
def recibir_datos(data: schemas.SensorDataCreate, db: Session = Depends(get_db)):
    alerta = None
    if data.bpm < 55:
        alerta = "⚠️ Ritmo cardíaco bajo (posible somnolencia)"
    elif data.bpm > 120:
        alerta = "⚠️ Ritmo cardíaco elevado (estrés o alarma física)"
    elif data.spo2 < 92:
        alerta = "⚠️ Nivel bajo de oxígeno"
    elif data.temperatura < 35.5:
        alerta = "⚠️ Temperatura corporal baja (relajación o somnolencia)"
    elif data.movimiento < 0.15:
        alerta = "⚠️ Falta de movimiento detectada"

    nuevo = models.SensorData(
        bpm=data.bpm,
        temperatura=data.temperatura,
        spo2=data.spo2,
        movimiento=data.movimiento,
        alerta=alerta,
        fecha_registro=datetime.now()
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/sensores/")
def listar_datos(db: Session = Depends(get_db)):
    return db.query(models.SensorData).all()
