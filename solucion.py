"""Contrato público del evaluador; no descarga pesos durante el import."""
from src.inference.engine import infer

def generar_sql(esquema: str, pregunta: str, ejecutar=None) -> str:
    return infer(esquema, pregunta, ejecutar)
