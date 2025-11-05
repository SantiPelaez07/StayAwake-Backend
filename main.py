from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
import models, schemas, database
from ia_model import predict_somnolence, predict_from_bytes, load_model_once, model_info
import shutil, os
from datetime import datetime

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="StayAwake Backend")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def warmup():
    try:
        load_model_once()
        print("Modelo IA cargado")
    except Exception as e:
        print(f"AVISO: modelo no cargado: {e}")

@app.get("/health")
def health():
    return {"ok": True, "service": "StayAwake Backend"}

@app.get("/model")
def model_meta():
    try:
        return {"loaded": True, **model_info()}
    except Exception as e:
        return {"loaded": False, "error": str(e)}

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
        bpm=data.bpm, temperatura=data.temperatura, spo2=data.spo2,
        movimiento=data.movimiento, alerta=alerta, fecha_registro=datetime.now()
    )
    db.add(nuevo); db.commit(); db.refresh(nuevo)
    return nuevo

@app.post("/imagen/")
async def procesar_imagen(file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg","image/png"):
        raise HTTPException(status_code=415, detail="Formato no soportado")
    os.makedirs("uploads", exist_ok=True)
    filepath = f"uploads/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        resultado = predict_somnolence(filepath)
        return {"mensaje": "Imagen procesada correctamente", "resultado": resultado, "archivo_guardado": filepath}
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Modelo no encontrado: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de inferencia: {e}")

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg","image/png"):
        raise HTTPException(status_code=415, detail="Formato no soportado")
    data = await file.read()
    try:
        resultado = predict_from_bytes(data)
        return {"resultado": resultado}
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Modelo no encontrado: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de inferencia: {e}")

@app.get("/sensores/")
def listar_datos(db: Session = Depends(get_db)):
    return db.query(models.SensorData).all()
