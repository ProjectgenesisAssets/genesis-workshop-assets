#!/usr/bin/env python3
"""Execute reviewed 3D generator edits via GitHub Actions, without running Blender locally.

The queue stores *concrete* edits. This program does not claim to be an art critic.
Every correction yields an immutable branch, audit receipt, and a workflow dispatch.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys

REPO = os.environ["GITHUB_REPOSITORY"]
QUEUE = Path("production/correction_queue.json")
REPORT = Path("reports/production_cycle.json")
ASSETS = {"door", "anvil", "forge", "bellows"}
WINDOW_END = dt.datetime(2026, 10, 27, 12, 0, tzinfo=dt.timezone.utc)
BRANCH_RE = re.compile(r"^production/[a-z0-9][a-z0-9_./-]*$")
TASK_RE = re.compile(r"^[a-z][a-z0-9-]{3,70}$")


def command(*args: str, check: bool = True) -> str:
    process = subprocess.run(args, text=True, capture_output=True)
    if check and process.returncode:
        raise RuntimeError(f"{' '.join(args[:3])} failed: {process.stderr[-1200:]}")
    return process.stdout.strip()


def github_json(*args: str):
    return json.loads(command("gh", *args))


def running_assets() -> set[str]:
    rows = github_json("run", "list", "--repo", REPO, "--limit", "100",
                       "--json", "headBranch,status")
    busy = set()
    for row in rows:
        if row.get("status") not in {"queued", "in_progress", "waiting", "requested", "pending"}:
            continue
        branch = row.get("headBranch") or ""
        for asset in ASSETS:
            if branch.startswith(f"production/{asset}-") or (asset == "anvil" and
                 branch.startswith("production/yunque-")) or branch.startswith(f"production/auto-{asset}-"):
                busy.add(asset)
    return busy


def branch_exists(branch: str) -> bool:
    # gh api returns exit nonzero for absent refs; no git overwrite or force push.
    return subprocess.run(["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
                          capture_output=True).returncode == 0


def valid_edit_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not str(path).startswith("scripts/"):
        raise ValueError("Correction may edit scripts/ only")
    if path.suffix != ".py" or not path.exists():
        raise ValueError("Correction must target an existing Python generator")
    return path


def process(task: dict, busy: set[str]) -> dict:
    asset = task["asset"]
    task_id = task["id"]
    base = task["base_branch"]
    workflow = task["workflow"]
    if asset not in ASSETS or not TASK_RE.fullmatch(task_id):
        raise ValueError("Invalid asset or task id")
    if not BRANCH_RE.fullmatch(base):
        raise ValueError("Invalid source branch")
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+\.yml", workflow):
        raise ValueError("Workflow must be a single .yml filename")
    changes = task["edits"]
    if not changes or len(changes) > 8:
        raise ValueError("Provide 1-8 concrete edits")
    target = f"production/auto-{asset}-{task_id}"
    if branch_exists(target):
        # Retry an interrupted dispatch only if GitHub has NO run for this immutable branch.
        previous=github_json("run","list","--repo",REPO,"--workflow",workflow,
                             "--branch",target,"--limit","10",
                             "--json","databaseId,status,conclusion")
        if previous:
            return {"id":task_id,"asset":asset,"status":"already_dispatched_or_preserved",
                    "branch":target,"run_id":previous[0]["databaseId"]}
        if asset in busy:
            return {"id":task_id,"asset":asset,"status":"waiting_active_render"}
        command("gh","workflow","run",workflow,"--repo",REPO,"--ref",target)
        busy.add(asset)
        return {"id":task_id,"asset":asset,"status":"dispatch_retried","branch":target}
    if asset in busy:
        return {"id": task_id, "asset": asset, "status": "waiting_active_render"}
    # Both generator and change plan must be attributable to an immutable source.
    command("git", "fetch", "--quiet", "origin", base)
    command("git", "checkout", "--quiet", "-B", target, "FETCH_HEAD")
    edited = []
    for edit in changes:
        path = valid_edit_path(edit["path"])
        old, new = edit["find"], edit["replace"]
        if not old or old == new:
            raise ValueError("No-op correction")
        source = path.read_text(encoding="utf-8")
        if source.count(old) != 1:
            raise ValueError(f"Expected one exact match in {path}, found {source.count(old)}")
        path.write_text(source.replace(old, new, 1), encoding="utf-8")
        command(sys.executable, "-m", "py_compile", str(path))
        edited.append(str(path))
    receipt = {
        "id": task_id, "asset": asset, "base_branch": base, "branch": target,
        "reason": task["reason"], "edits": edited,
        "approval": "NOT_ARTISTICALLY_APPROVED",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat()
    }
    # The dispatch workflow must exist on default AND on this isolated source ref.
    # Copy ONLY the shared worker/QA from main; never import another asset generator.
    if workflow == "production-asset-iteration.yml":
        command("git","fetch","--quiet","origin","main")
        for shared in (".github/workflows/production-asset-iteration.yml",
                       "scripts/production_asset_qa.py"):
            body=command("git","show",f"origin/main:{shared}")+"\n"
            destination=Path(shared)
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_text(body,encoding="utf-8")
            edited.append(shared)
    out = Path("production/receipts") / f"{asset}-{task_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    command("git", "add", *edited, str(out))
    if not command("git", "diff", "--cached", "--name-only"):
        raise ValueError("No source changes")
    command("git", "-c", "user.name=genesis-cycle[bot]",
            "-c", "user.email=genesis-cycle@users.noreply.github.com",
            "commit", "-qm", f"Production correction {asset} {task_id}")
    command("git", "push", "origin", f"HEAD:refs/heads/{target}")
    try:
        command("gh", "workflow", "run", workflow, "--repo", REPO, "--ref", target)
    except Exception as exc:
        return {"id": task_id, "asset": asset, "status": "dispatch_failed",
                "branch": target, "error": str(exc)}
    busy.add(asset)
    return {"id": task_id, "asset": asset, "status": "dispatched", "branch": target}


def main() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    tasks = json.loads(QUEUE.read_text(encoding="utf-8")).get("tasks", [])
    if len(tasks) > 50:
        raise ValueError("Queue too large")
    results = []
    if now >= WINDOW_END:
        results.append({"status": "window_closed"})
    else:
        busy = running_assets()
        seen = set()
        for task in tasks:
            ident = (task.get("asset"), task.get("id"))
            if ident in seen:
                results.append({"id": ident[1], "status": "duplicate_queue_entry"})
                continue
            seen.add(ident)
            try:
                results.append(process(task, busy))
            except Exception as exc:
                results.append({"id": task.get("id"), "asset": task.get("asset"),
                                "status": "blocked", "error": str(exc)})
            finally:
                command("git", "checkout", "--quiet", "-f", os.environ.get("GITHUB_REF_NAME", "main"),
                        check=False)
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps({"checked_utc": now.isoformat(), "results": results},
                                 indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
