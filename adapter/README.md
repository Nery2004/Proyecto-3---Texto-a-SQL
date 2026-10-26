# Adapter final

Esta carpeta no contiene pesos sin entrenar. El adapter final solo se instala
después de dos entrenamientos completos y su comparación real. Con
usar_adapter=true, la inferencia falla explícitamente si falta adapter_config.json.
Nunca se sustituye silenciosamente por el modelo base.
