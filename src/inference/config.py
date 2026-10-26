import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWED = {"Qwen/Qwen2.5-Coder-1.5B-Instruct", "Qwen/Qwen2.5-Coder-0.5B-Instruct", "Qwen/Qwen3-1.7B"}

def load_config():
    path = Path(os.environ.get("TEXT2SQL_CONFIG", ROOT / "config.json")).resolve()
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("modelo_base") not in ALLOWED:
        raise ValueError("Modelo base no permitido")
    if type(value.get("usar_adapter")) is not bool:
        raise ValueError("usar_adapter debe ser booleano")
    if type(value.get("semilla")) is not int or value["semilla"] < 0:
        raise ValueError("semilla debe ser un entero no negativo")
    if not isinstance(value.get("adapter"), str) or not value["adapter"]:
        raise ValueError("Ruta adapter inválida")
    adapter = (path.parent / value["adapter"]).resolve()
    if value["usar_adapter"] and not (adapter / "adapter_config.json").is_file():
        raise FileNotFoundError(f"Adapter entrenado ausente: {adapter}. Ejecute el entrenamiento primero.")
    value["adapter"] = str(adapter)
    return value
