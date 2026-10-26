import json
import pytest
from src.inference.config import load_config
from src.inference import engine

def make_config(tmp_path, monkeypatch, **updates):
    config={"modelo_base":"Qwen/Qwen2.5-Coder-1.5B-Instruct","adapter":"adapter/","usar_adapter":False,"semilla":2026}
    config.update(updates)
    path=tmp_path/'config.json'
    path.write_text(json.dumps(config),encoding='utf-8')
    monkeypatch.setenv('TEXT2SQL_CONFIG',str(path))
    return path

@pytest.mark.parametrize('updates',[{'modelo_base':'other'},{'usar_adapter':1},{'semilla':True},{'semilla':-1},{'adapter':''}])
def test_invalid(tmp_path,monkeypatch,updates):
    make_config(tmp_path,monkeypatch,**updates)
    with pytest.raises(ValueError): load_config()

def test_adapter_required(tmp_path,monkeypatch):
    make_config(tmp_path,monkeypatch,usar_adapter=True)
    with pytest.raises(FileNotFoundError): load_config()
    (tmp_path/'adapter').mkdir()
    (tmp_path/'adapter/adapter_config.json').write_text('{}')
    assert load_config()['adapter']==str((tmp_path/'adapter').resolve())

def test_model_cache_and_modes(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(engine,'Runtime',lambda config: calls.append(config) or object())
    engine._cached.cache_clear()
    path=make_config(tmp_path,monkeypatch)
    first=engine.get_runtime()
    assert engine.get_runtime() is first
    assert len(calls)==1 and calls[0]['usar_adapter'] is False
    (tmp_path/'adapter').mkdir()
    (tmp_path/'adapter/adapter_config.json').write_text('{}')
    config=json.loads(path.read_text());config['usar_adapter']=True
    path.write_text(json.dumps(config))
    assert engine.get_runtime() is not first
    assert len(calls)==2 and calls[1]['usar_adapter'] is True
    engine._cached.cache_clear()
