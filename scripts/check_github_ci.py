"""Consulta evidencia real de Actions sin exponer credenciales del gestor Git."""
import json
from pathlib import Path
import subprocess
import urllib.request
import urllib.error

def main():
    proc=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True)
    values=dict(line.split('=',1) for line in proc.stdout.splitlines() if '=' in line)
    token=values.get('password')
    if not token:raise RuntimeError('No hay credenciales disponibles para consultar Actions')
    request=urllib.request.Request('https://api.github.com/repos/Nery2004/Proyecto-3---Texto-a-SQL/actions/runs?per_page=5',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'text2sql-audit'})
    try:
        with urllib.request.urlopen(request) as response:data=json.load(response)
        report={'runs':[{k:r.get(k) for k in ['head_sha','name','status','conclusion','html_url']} for r in data['workflow_runs']]}
    except urllib.error.HTTPError as exc:report={'http_error':exc.code}
    Path('docs/github_ci.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
