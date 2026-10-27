#!/usr/bin/env python3
"""Project Genesis: per-asset Actions state, no false artistic approval."""
import json, os, pathlib, subprocess, datetime
REPO = os.environ["GITHUB_REPOSITORY"]
WORKFLOW = "night-production-qa.yml"
ASSETS = ("door", "anvil", "forge", "bellows")
def gh(*args):
    p=subprocess.run(["gh",*args],capture_output=True,text=True)
    if p.returncode:
        raise RuntimeError("gh " + " ".join(args) + ": " + p.stderr[-600:])
    return json.loads(p.stdout)
def main():
    runs=gh("run","list","--repo",REPO,"--workflow",WORKFLOW,"--limit","5",
            "--json","databaseId,status,conclusion,createdAt,headSha,url")
    recent=runs[0] if runs else None
    jobs=[]
    if recent:
        result=gh("api",f"repos/{REPO}/actions/runs/{recent['databaseId']}/jobs")
        jobs=result.get("jobs",[])
    statuses=[]
    for a in ASSETS:
        matches=[j for j in jobs if a in j.get("name","").lower()]
        j=matches[-1] if matches else {}
        statuses.append({"asset":a,"status":j.get("status","no_job"),"conclusion":j.get("conclusion"),
            "job_url":j.get("html_url"),"run_id":recent.get("databaseId") if recent else None})
    rep={"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "workflow":WORKFLOW,"latest_run":recent,"assets":statuses,
        "next_action":"Commit a real generator improvement to launch a new iteration",
        "automatic_artistic_approval":False,
        "warning":"A green render is not an 8/10 asset. No identical-version relaunches."}
    pathlib.Path("reports").mkdir(exist_ok=True)
    pathlib.Path("reports/overnight_status.json").write_text(json.dumps(rep,indent=2)+"\n")
    lines=["# Project Genesis — control por asset", "",
        f"Comprobado: {rep['checked_at_utc']}","",
        "| Asset | Ejecucion | Estado |", "|---|---|---|"]
    for x in statuses:
        link="[GitHub]("+x["job_url"]+")" if x["job_url"] else "Sin ejecucion"
        lines.append(f"| {x['asset']} | {link} | {x['status']} / {x['conclusion'] or '—'} |")
    lines.extend(["","**No se aprueba calidad artística ni se relanza código idéntico sin cambios.**"])
    pathlib.Path("reports/overnight_status.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":main()
