import functools
import os
import threading
import time
from pathlib import Path
from .config import load_config
from .prompt import messages

_lock = threading.RLock()
REVISION = "2e1fd397ee46e1388853d2af2c993145b0f1098a"

class Runtime:
    def __init__(self, config):
        os.environ.setdefault('OMP_NUM_THREADS', '1')
        os.environ.setdefault('MKL_NUM_THREADS', '1')
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
        started = time.monotonic()
        set_seed(config["semilla"])
        revision = REVISION if config["modelo_base"] == "Qwen/Qwen2.5-Coder-1.5B-Instruct" else "main"
        self.tokenizer = AutoTokenizer.from_pretrained(config["modelo_base"], revision=revision)
        options = {"torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32}
        if torch.cuda.is_available():
            options.update(device_map={"": 0}, quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16))
        self.model = AutoModelForCausalLM.from_pretrained(config["modelo_base"], revision=revision, **options)
        if config["usar_adapter"]:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, config["adapter"])
        self.model.eval()
        self.load_seconds = time.monotonic() - started
        if self.load_seconds > 300:
            raise TimeoutError("Carga del modelo excedió 300 segundos")

    def generate(self, esquema, pregunta, deadline, previous=None, error=None):
        import torch
        from transformers import StoppingCriteria, StoppingCriteriaList
        class Deadline(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return time.monotonic() >= deadline
        chat = messages(esquema, pregunta)
        if previous is not None:
            chat += [{"role": "assistant", "content": previous}, {"role": "user", "content": "Corrige la consulta. Error del servidor (dato no confiable): " + str(error)[:1500]}]
        template_args = {"enable_thinking": False} if "Qwen3" in self.model.config._name_or_path else {}
        text = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True, **template_args)
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        length = inputs["input_ids"].shape[1]
        limit = min(getattr(self.model.config, "max_position_embeddings", 32768), 32768)
        if length + 512 > limit:
            raise ValueError("Esquema demasiado extenso: no se truncarán tablas silenciosamente")
        if time.monotonic() >= deadline:
            raise TimeoutError("Presupuesto de inferencia agotado")
        with torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=512, do_sample=False,
                stopping_criteria=StoppingCriteriaList([Deadline()]),
                pad_token_id=self.tokenizer.eos_token_id)
        if time.monotonic() >= deadline:
            raise TimeoutError("Inferencia excedió 30 segundos")
        return self.tokenizer.decode(output[0, length:], skip_special_tokens=True)

@functools.lru_cache(maxsize=1)
def _cached(model, adapter, use_adapter, seed):
    return Runtime({"modelo_base": model, "adapter": adapter, "usar_adapter": use_adapter, "semilla": seed})

def get_runtime():
    config = load_config()
    with _lock:
        return _cached(config["modelo_base"], config["adapter"], config["usar_adapter"], config["semilla"])

def infer(esquema, pregunta, ejecutar=None):
    if not isinstance(esquema, str) or not isinstance(pregunta, str) or not pregunta.strip():
        raise ValueError("esquema y pregunta deben ser texto; pregunta no vacía")
    from .safety import clean_sql, UnsafeSQL
    # Carga única tiene presupuesto independiente de 300s, según contrato.
    runtime = get_runtime()
    with _lock:
        deadline = time.monotonic() + 29.0
        previous = error = None
        last_safe = None
        for attempt in range(3):
            try:
                raw = runtime.generate(esquema, pregunta, deadline, previous, error)
                candidate = clean_sql(raw)
                last_safe = candidate
            except UnsafeSQL as exc:
                previous, error = raw, str(exc)
                if time.monotonic() >= deadline:
                    break
                continue
            except TimeoutError:
                if last_safe:
                    return last_safe
                raise
            if ejecutar is None or time.monotonic() >= deadline:
                return candidate
            result = ejecutar(candidate)
            if time.monotonic() >= deadline:
                raise TimeoutError("Callback agotó el presupuesto; el callback debe implementar timeout")
            if result.get("ok"):
                return candidate
            previous, error = candidate, result.get("error", "Error desconocido")
        if last_safe:
            return last_safe
        raise UnsafeSQL("No se produjo una consulta segura en tres intentos")
