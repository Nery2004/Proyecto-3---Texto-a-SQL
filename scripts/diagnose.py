import importlib
import json
import platform
import os
from pathlib import Path

def main():
    result = {"python": platform.python_version()}
    for name in ["torch", "transformers", "peft", "accelerate", "bitsandbytes", "sqlglot", "mysql.connector"]:
        try:
            module = importlib.import_module(name)
            result[name] = getattr(module, "__version__", "importable")
            if name == "torch":
                result["cuda"] = module.cuda.is_available()
                result["gpu"] = module.cuda.get_device_name(0) if result["cuda"] else None
        except Exception as exc:
            result[name] = {"error": str(exc)}
    result["adapter_weights"] = Path("adapter/adapter_model.safetensors").is_file()
    try:
        from src.data.mysql import MySQLExecutor
        with MySQLExecutor('universidad') as database:
            result['mysql'] = database.version
    except Exception as exc:
        result['mysql'] = {'error': str(exc)}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
