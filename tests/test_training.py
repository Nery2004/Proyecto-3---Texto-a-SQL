import json

import pytest

from src.training.pipeline import encode_example, load_records


def test_configs_only_rank_changes():
    from pathlib import Path
    a, b = [json.loads(Path(f'configs/lora_{x}.json').read_text()) for x in 'ab']
    assert (a.pop('rank'), b.pop('rank')) == (8, 16)
    a.pop('output_dir'); b.pop('output_dir')
    assert a == b


def test_training_rejects_unexecuted_data(tmp_path):
    path = tmp_path / 'data.jsonl'
    row = dict(id='id', schema_id='s', esquema='CREATE TABLE t (id INT)', pregunta='IDs', sql='SELECT id FROM t', validado=False, mysql_version='8.4.10')
    path.write_text('\n'.join(json.dumps(dict(row, id=str(i))) for i in range(2000)))
    with pytest.raises(ValueError, match='sin evidencia'):
        load_records(path)


def test_assistant_only_loss_and_no_truncation():
    class Tokenizer:
        def apply_chat_template(self, messages, tokenize, add_generation_prompt):
            return [1, 2, 3] if add_generation_prompt else [1, 2, 3, 4, 5]
    row = dict(id='example', esquema='CREATE TABLE t (id INT)', pregunta='IDs', sql='SELECT id FROM t')
    encoded = encode_example(row, Tokenizer(), 5)
    assert encoded['labels'] == [-100, -100, -100, 4, 5]
    with pytest.raises(ValueError, match='no se trunca'):
        encode_example(row, Tokenizer(), 4)
