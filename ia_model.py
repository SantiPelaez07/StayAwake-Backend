# ia_model.py
import io, os
from typing import Tuple
import numpy as np
from PIL import Image
import tensorflow as tf

MODEL_PATH = os.getenv("EYE_MODEL_PATH", "/modelosia/2018_12_17_22_58_35.h5")
# Usa 24x24 gris si tu modelo proviene del eye_blink_detector clásico.
# INPUT_SIZE: Tuple[int, int] = (24, 24); GRAYSCALE = True
INPUT_SIZE: Tuple[int, int] = (64, 64); GRAYSCALE = False
THRESHOLD = float(os.getenv("DROWSY_THRESHOLD", "0.5"))

_model = None

def load_model_once():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Modelo no encontrado en: {MODEL_PATH}")
        _model = tf.keras.models.load_model(MODEL_PATH)
    return _model

def _preprocess_image_bytes(img_bytes: bytes, size: Tuple[int, int] = INPUT_SIZE) -> np.ndarray:
    img = Image.open(io.BytesIO(img_bytes))
    img = img.convert("L" if GRAYSCALE else "RGB").resize(size)
    arr = np.asarray(img, dtype="float32") / 255.0
    if GRAYSCALE:
        arr = np.expand_dims(arr, axis=-1)  # [H,W,1]
    return np.expand_dims(arr, axis=0)      # [1,H,W,C]

def predict_from_bytes(img_bytes: bytes) -> dict:
    model = load_model_once()
    x = _preprocess_image_bytes(img_bytes)
    pred = model.predict(x, verbose=0)
    # Si tu salida es [1] usa [0][0]; si es softmax [open,closed], ajusta índice
    prob = float(pred[0][0])
    return {
        "somnolencia": prob > THRESHOLD,
        "probabilidad": prob,
        "mensaje": "😴 Ojos cerrados detectados" if prob > THRESHOLD else "😀 Ojos abiertos detectados",
    }

def predict_somnolence(image_path: str) -> dict:
    with open(image_path, "rb") as f:
        return predict_from_bytes(f.read())

def model_info() -> dict:
    m = load_model_once()
    try:
        in_shape = tuple(m.input_shape)
        out_shape = tuple(m.output_shape)
    except Exception:
        in_shape = out_shape = None
    return {"path": MODEL_PATH, "input_shape": in_shape, "output_shape": out_shape, "threshold": THRESHOLD}
