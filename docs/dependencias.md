# Dependencias y compatibilidad

Entorno objetivo: Python 3.10–3.12, Linux Colab T4. requirements.txt fija torch 2.6.0, Transformers 4.48.3, PEFT 0.14.0, Accelerate 1.3.0 y bitsandbytes 0.45.2. Son versiones conservadoras de la misma generación; no se requiere TRL. Se usa Trainer directamente para controlar la máscara de pérdida.

Fuentes primarias consultadas el 25 de octubre de 2026:

- [Qwen quickstart](https://qwen.readthedocs.io/en/v2.5/getting_started/quickstart.html): Qwen2.5 requiere Transformers >=4.37.
- [PEFT 0.14.0 setup.py](https://github.com/huggingface/peft/blob/v0.14.0/setup.py): Python >=3.9, torch >=1.13, Accelerate >=0.21 y Hub >=0.25.
- [Transformers 4.48.3 setup.py](https://github.com/huggingface/transformers/blob/v4.48.3/setup.py): restricciones de tokenizers y Hub.
- [bitsandbytes 0.45.2](https://huggingface.co/docs/bitsandbytes/v0.45.2/installation): CUDA 11–12.6; NF4 soportado en T4.
- [PEFT cuantización](https://huggingface.co/docs/peft/v0.14.0/developer_guides/quantization): prepare_model_for_kbit_training antes de insertar LoRA.
- [Matriz oficial PyTorch](https://pytorch.org/get-started/previous-versions/): torch 2.6.0 se combina con torchvision 0.21.0 y torchaudio 2.6.0.

Esto comprueba compatibilidad declarada, no demuestra una ejecución completa en T4. El notebook instala wheels CUDA 12.4 de PyTorch y requirements, ejecuta pip check e imports reales. En Linux se fijan también torchvision/torchaudio compatibles para alinear los paquetes preinstalados en Colab con torch; no se usan para el modelo de texto. En Windows limpio no se instalan. Otros paquetes ajenos preinstalados pueden requerir runtime limpio o entorno virtual; no se ha afirmado verificar una imagen Colab específica. Si un kernel ya importó torch, reiniciar el runtime después de instalar antes de continuar.

Verificación local real: instalación en un venv Python 3.12 Windows, seguida de `pip check`: `No broken requirements found.` Evidencia en `resultados/metricas/pip_check.txt` y versiones instaladas en `dependencias_instaladas.txt`. La importación del stack GPU y la precarga tienen su evidencia separada; `pip check` no prueba carga CUDA.
