from pydantic import BaseModel
from datetime import datetime

class SensorDataCreate(BaseModel):
    bpm: float
    temperatura: float
    spo2: float
    movimiento: float

class SensorDataResponse(SensorDataCreate):
    id: int
    alerta: str | None
    fecha_registro: datetime

    class Config:
        orm_mode = True

