"""Ajusta privacidad con credenciales del gestor Git sin imprimir secretos."""
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

def main():
    proc = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n", text=True, capture_output=True)
    values = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
    token = values.get("password")
    if not token:
        print("No hay credenciales Git disponibles para API de administración")
        return
    url = "https://api.github.com/repos/Nery2004/Proyecto-3---Texto-a-SQL"
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "User-Agent": "text2sql-project"}
    evidence = {}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            repo = json.load(response)
        evidence["before"] = repo["visibility"]
        evidence["admin"] = repo.get("permissions", {}).get("admin", False)
        if evidence["admin"] and not repo["private"]:
            req = urllib.request.Request(url, headers=headers, data=json.dumps({"private": True}).encode(), method="PATCH")
            with urllib.request.urlopen(req) as response:
                repo = json.load(response)
        evidence["after"] = repo["visibility"]
        evidence["teacher_access"] = "No verificado: falta usuario GitHub del docente"
    except urllib.error.HTTPError as exc:
        evidence["http_error"] = exc.code
    Path("docs/github_access.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence))

if __name__ == "__main__":
    main()
