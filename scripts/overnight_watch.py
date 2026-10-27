#!/usr/bin/env python3
"""GitHub Actions overnight watch. Never approves art and never reruns unchanged meshes."""
import json,os,subprocess,datetime,pathlib
REPO=os.environ["GITHUB_REPOSITORY"]
FILES=[
 ("puerta V003","puerta-herreria-art-master-v003.yml","previews/door_v003/front.png"),
 ("trío V002","genesis-hero-trio-v002.yml","previews/heroes_v002/anvil/front.png"),
 ("tanda nocturna","night-production-qa.yml",None),
]
def gh(*args):
    p=subprocess.run(["gh",*args],capture_output=True,text=True,check=False)
    if p.returncode: raise RuntimeError("gh "+ " ".join(args)+": "+p.stderr[-1200:])
    return json.loads(p.stdout)
def main():
    checks=[]
    active=False
    for name,workflow,preview in FILES:
        runs=gh("run","list","--repo",REPO,"--workflow",workflow,"--limit","3",
                "--json","databaseId,status,conclusion,createdAt,headSha,url,attempt")
        top=runs[0] if runs else None
        if top and top["status"] in ("queued","in_progress","waiting","requested","pending"):
            active=True
        checks.append({"asset":name,"workflow":workflow,"latest":top,
                       "preview_present":bool(preview and pathlib.Path(preview).is_file())})
    report={"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "runs":checks,
            "policy":"No automatic art approval. No rerun of unchanged model. Failed renders require diagnosis/correction.",
            "next_action":"Review PNGs and commit improved script after human visual QA; launch on push."}
    pathlib.Path("reports").mkdir(exist_ok=True)
    pathlib.Path("reports/overnight_status.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    lines=["# Project Genesis — control de producción", "",f"Revisado: {report['checked_at_utc']}","",
           "| Activo | Estado | Ejecución |", "| --- | --- | --- |"]
    for x in checks:
        r=x["latest"]
        if r:
            lines.append(f"| {x['asset']} | {r['status']} / {r['conclusion'] or '—'} | [Ver]({r['url']}) |")
        else:lines.append(f"| {x['asset']} | Sin ejecuciones | — |")
    lines+=["","No hay aprobación artística automática ni bucles de renders idénticos.",
            "Al finalizar se deben inspeccionar las cuatro vistas y corregir el generador para una nueva versión."]
    pathlib.Path("reports/overnight_status.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
