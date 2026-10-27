#!/usr/bin/env python3
"""Read the latest *real independent* GitHub Actions jobs, not legacy V002 QA.

This monitor never edits Blender sources or awards aesthetic approval.
Each asset is matched to its newest production branch and workflow run.
"""
import datetime
import json
import os
import pathlib
import re
import subprocess
import urllib.parse

REPO=os.environ["GITHUB_REPOSITORY"]
ASSETS=("door","anvil","forge","bellows")
BRANCH_MATCH={
    "door":re.compile(r"^production/door-v\d+"),
    "anvil":re.compile(r"^production/yunque-v\d+"),
    "forge":re.compile(r"^production/forge-v\d+"),
    "bellows":re.compile(r"^production/bellows-v\d+"),
}
def gh(*args):
    p=subprocess.run(["gh",*args],capture_output=True,text=True)
    if p.returncode:
        raise RuntimeError("gh "+" ".join(args)+": "+p.stderr[-500:])
    return json.loads(p.stdout)
def comparison(asset,branch):
    match=re.search(r"-v(\d+)",branch)
    if not match or asset=="anvil":
        return None
    version="v"+match.group(1)
    path=f"reports/{asset}_{version}/comparison.json"
    query=urllib.parse.quote(branch,safe="")
    try:
        payload=gh("api",f"repos/{REPO}/contents/{path}?ref={query}")
        import base64
        data=base64.b64decode(payload["content"])
        record=json.loads(data)
        return {"path":path,
                "technical_visual_gate":record.get("technical_visual_gate"),
                "objective_defects":record.get("objective_defects"),
                "artist_approved":False}
    except (RuntimeError,KeyError,ValueError):
        return None
def main():
    runs=gh("run","list","--repo",REPO,"--limit","100",
            "--json","databaseId,status,conclusion,createdAt,headSha,headBranch,url,workflowName")
    statuses=[]
    for asset in ASSETS:
        matches=[r for r in runs if BRANCH_MATCH[asset].search(r.get("headBranch") or "")]
        matches.sort(key=lambda r:r.get("createdAt") or "",reverse=True)
        current=matches[0] if matches else None
        branch=current.get("headBranch") if current else None
        receipt=comparison(asset,branch) if branch and current["conclusion"]=="success" else None
        statuses.append({"asset":asset,"latest_branch":branch,
            "status":current.get("status") if current else "no_run",
            "conclusion":current.get("conclusion") if current else None,
            "run_id":current.get("databaseId") if current else None,
            "run_url":current.get("url") if current else None,
            "source_sha":current.get("headSha") if current else None,
            "comparison_receipt":receipt,"artist_approved":False})
    rep={"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "source":"Newest real production/door, yunque, forge, bellows workflow runs",
         "assets":statuses,"automatic_artistic_approval":False,
         "warning":"Green Actions or pixel deltas do not prove artistic quality."}
    pathlib.Path("reports").mkdir(exist_ok=True)
    pathlib.Path("reports/overnight_status.json").write_text(json.dumps(rep,indent=2)+"\n")
    lines=["# Project Genesis - latest independent production checks","",
           f"UTC: {rep['checked_at_utc']}","",
           "| Asset | Branch | Latest run | Technical gate |",
           "|---|---|---|---|"]
    for row in statuses:
        link=f"[Actions]({row['run_url']})" if row["run_url"] else "None"
        receipt=row["comparison_receipt"]
        gate=receipt["technical_visual_gate"] if receipt else "pending/not published"
        lines.append(f"| {row['asset']} | {row['latest_branch'] or '-'} | {link}: {row['status']} / {row['conclusion'] or '-'} | {gate} |")
    lines+=["","**No artistic approvals.** An Actions success only confirms pipeline completion."]
    pathlib.Path("reports/overnight_status.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":
    main()
