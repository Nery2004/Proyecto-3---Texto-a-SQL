"""Real forward/backward precision diagnostic, never saves an adapter."""
import argparse
import json
import math
import os
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--attention', choices=['eager', 'sdpa'], default='sdpa')
    parser.add_argument('--compute-dtype', choices=['float16', 'float32', 'bfloat16'], default='float16')
    parser.add_argument('--amp', action='store_true')
    args = parser.parse_args()
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    os.environ.setdefault('MKL_NUM_THREADS', '1')
    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
    from src.training.pipeline import load_records, encode_example
    cfg = json.loads(Path('configs/lora_a.json').read_text())
    report = {'attention': args.attention, 'compute_dtype': args.compute_dtype, 'amp': args.amp, 'estado': 'iniciado', 'batches': []}
    path = Path(f'resultados/metricas/preflight_{args.attention}_{args.compute_dtype}_{args.amp}.json')
    started = time.perf_counter()
    try:
        set_seed(cfg['seed'])
        dtype = getattr(torch, args.compute_dtype)
        tokenizer = AutoTokenizer.from_pretrained(cfg['model'], revision=cfg['revision'], local_files_only=True)
        rows = load_records(cfg['dataset'])
        encoded = [encode_example(r, tokenizer, cfg['max_length']) for r in rows]
        indices = [0, 121, max(range(len(encoded)), key=lambda i: len(encoded[i]['input_ids']))]
        model = AutoModelForCausalLM.from_pretrained(cfg['model'], revision=cfg['revision'], local_files_only=True, device_map={'': 0}, torch_dtype=dtype, attn_implementation=args.attention, quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype))
        model.config.use_cache = False
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
        model = get_peft_model(model, LoraConfig(r=cfg['rank'], lora_alpha=cfg['alpha'], lora_dropout=cfg['dropout'], target_modules=cfg['target_modules'], bias='none', task_type='CAUSAL_LM'))
        model.train()
        optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=cfg['learning_rate'])
        torch.cuda.reset_peak_memory_stats()
        for i in indices:
            batch = {k: torch.tensor([v], device='cuda') for k, v in encoded[i].items()}
            model.zero_grad(set_to_none=True)
            with torch.autocast('cuda', dtype=torch.float16, enabled=args.amp):
                loss = model(**batch).loss
            loss.backward()
            norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
            value = float(loss)
            observation = {'id': rows[i]['id'], 'tokens': len(encoded[i]['input_ids']), 'loss': value if math.isfinite(value) else str(value), 'grad_norm': norm if math.isfinite(norm) else str(norm), 'finito': math.isfinite(value) and math.isfinite(norm)}
            if observation['finito']:
                optimizer.step()
                observation['lora_b_no_cero_tras_optimizer'] = any(bool(torch.count_nonzero(p)) for name, p in model.named_parameters() if 'lora_B' in name)
            report['batches'].append(observation)
            print(observation, flush=True)
        report.update(estado='completado', todos_finitos=all(x['finito'] for x in report['batches']), vram_max_bytes=torch.cuda.max_memory_allocated())
    except Exception as exc:
        report.update(estado='fallido', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['segundos'] = time.perf_counter() - started
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')


if __name__ == '__main__':
    main()
