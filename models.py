from sqlalchemy import Column, Integer, Float, String, DateTime
from database import Base
from datetime import datetime

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    bpm = Column(Float)
    temperatura = Column(Float)
    spo2 = Column(Float)
    movimiento = Column(Float)
    alerta = Column(String, nullable=True)
    fecha_registro = Column(DateTime, default=datetime.now)

