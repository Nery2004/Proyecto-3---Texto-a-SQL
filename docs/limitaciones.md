# Límites del sistema

La inspección AST reduce SQL peligroso y se respalda con un usuario MySQL que
solo tiene SELECT. No demuestra que una consulta responda a la pregunta.
Los comentarios del esquema se envían como datos dentro de JSON, pero la
resistencia a prompt injection del modelo no tiene garantía formal.

La generación usa un plazo común de 29 segundos y un máximo de 512 tokens.
La comprobación se realiza entre pasos de generación; un kernel GPU o callback
externo bloqueado no se puede interrumpir de forma segura desde Python. El
callback debe imponer su propio timeout; el ejecutor propio limita MySQL a 5s.
El evaluador registra y penaliza cualquier ejecución que supere 30s.

El esquema no se trunca: si excede el contexto se rechaza explícitamente.
La carga inicial se mide por separado con límite de 300s; las descargas de pesos
pueden excederlo en una red lenta, por lo que se recomienda precargar caché Colab.

Los fixtures son pequeños y sintéticos. La ejecución comprueba sintaxis y
referencias, pero no garantiza diversidad ni correspondencia semántica completa.
Las propuestas de validación son de IA y requieren autoría/revisión humana real.
No existe evidencia de colaboración humana durante dos semanas.
