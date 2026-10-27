#!/usr/bin/env python3
"""Prepare an evidence-only artistic review handoff after real GitHub Blender runs.

This script NEVER invents corrections or claims artistic approval.
GitHub automation/AI consumes the manifest and contact sheet, writes bounded
source edits to correction_queue.json, and starts the next genuine Blender run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ASSETS = ("forge", "bellows", "door", "anvil")
VIEWS = ("front", "three_quarter", "rear", "detail")
# Legacy asset pipelines use different camera names; normalize into 4 review slots.
VIEW_FILES = {
    "forge": ("front", "three_quarter", "rear", "detail"),
    "bellows": ("front", "three_quarter", "rear", "detail"),
    "door": ("front", "three_quarter", "rear", "side"),
    "anvil": ("front", "hero", "rear", "top"),
}
REPO = os.environ.get("GITHUB_REPOSITORY", "ProjectgenesisAssets/genesis-workshop-assets")
OUTPUT = Path("reports/auto_review")
CUTOFF = dt.datetime(2026, 10, 27, 12, tzinfo=dt.timezone.utc)
TARGET_NAMES = {
    "forge": ("forge",),
    "bellows": ("bellows",),
    "door": ("door",),
    "anvil": ("anvil", "yunque"),
}

def api(path: str) -> dict:
    cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json", path]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

def read_blob(branch: str, path: str) -> bytes | None:
    # GitHub Contents API omits inline base64 for PNGs over 1MB.
    # Download the actual image bytes using the canonical GitHub raw URL.
    path_fragment = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    url = "https://raw.githubusercontent.com/" + REPO + "/" + urllib.parse.quote(branch, safe="/") + "/" + path_fragment
    headers = {"User-Agent": "GenesisArtReview/1.0"}
    token = os.environ.get("GH_TOKEN", "")
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read(12_000_000)
        if not data.startswith(bytes.fromhex("89504e470d0a1a0a")):
            raise ValueError("Preview is not a PNG: " + path)
        return data
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print("PREVIEW_DOWNLOAD_ERROR", branch, path, str(exc)[:120])
        return None

def candidates() -> dict:
    # Use exact production branch prefixes. Substring matching falsely treated
    # door-v013-dark-FORGED-iron as a FORGE candidate, corrupting the contact sheet.
    prefixes = {
        "forge": ("production/auto-forge-", "production/forge-"),
        "bellows": ("production/auto-bellows-", "production/bellows-"),
        "door": ("production/auto-door-", "production/door-"),
        "anvil": ("production/auto-anvil-", "production/anvil-", "production/yunque-"),
    }
    runs = []
    for page in range(1, 5):
        batch = api("/repos/" + REPO + f"/actions/runs?per_page=100&page={page}").get("workflow_runs", [])
        runs.extend(batch)
        if len(batch) < 100:
            break
    # Older approved-shape candidates must not disappear when >100 unrelated
    # workflows run; scan paginated history, then rank by completion time.
    runs.sort(key=lambda run: run.get("updated_at") or "", reverse=True)
    found = {}
    for run in runs:
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        branch = (run.get("head_branch") or "").lower()
        for asset, accepted_prefixes in prefixes.items():
            if asset in found or not branch.startswith(accepted_prefixes):
                continue
            found[asset] = {"branch": run["head_branch"], "run_id": run["id"],
                            "run_url": run["html_url"], "commit": run["head_sha"],
                            "completed_at": run.get("updated_at")}
    return found

def find_four_views(asset: str, branch: str) -> tuple[str | None, dict]:
    # Never guess that the four images exist: inspect the actual repo tree.
    tree = api("/repos/" + REPO + "/git/trees/"
               + urllib.parse.quote(branch, safe="") + "?recursive=1")
    files = [x["path"] for x in tree.get("tree", []) if x.get("type") == "blob"]
    roots = set()
    for path in files:
        if not path.startswith("previews/") or not path.endswith("/front.png"):
            continue
        prefix = path[:-len("/front.png")]
        if asset in prefix.lower() or (asset == "anvil" and "yunque" in prefix.lower()):
            roots.add(prefix)
    matches = []
    for prefix in roots:
        # Auto-door candidates render a real hardware detail; legacy door
        # branches supply a side orthographic view instead. Never mix them.
        source_views = (("front","three_quarter","rear","detail")
                        if asset == "door" and branch.startswith("production/auto-door-")
                        else VIEW_FILES[asset])
        views = {slot: f"{prefix}/{source}.png"
                 for slot, source in zip(VIEWS, source_views)
                 if f"{prefix}/{source}.png" in files}
        if len(views) == 4:
            matches.append((prefix, views))
    if not matches:
        return None, {}
    # Match the completed candidate task exactly. Lexicographic sorting alone
    # can wrongly select inherited V014 (smithy) over new V015 (ashlar).
    task_prefix = f"production/auto-{asset}-"
    expected = ("previews/production_auto/" + asset + "_" +
                branch[len(task_prefix):]) if branch.startswith(task_prefix) else None
    # New auto-iteration branches inherit earlier previews. Never present
    # inherited V014/V015 pictures as if they were the new candidate's renders.
    if expected:
        exact = [pair for pair in matches if pair[0] == expected]
        if not exact:
            return None, {}
        return exact[0]
    matches.sort(key=lambda pair: ("/production_auto/" in pair[0], pair[0]))
    return matches[-1]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    entries = candidates()
    manifest = {"schema": 1, "generated_at": now.isoformat(),
                "deadline_utc": CUTOFF.isoformat(),
                "asset_candidates": {}, "automatic_art_approval": False,
                "correction_queue": "production/correction_queue.json",
                "review_instructions": [
                    "Inspect real 4-view images against previous candidate and reference.",
                    "Write specific silhouette, material, shading and usability defects.",
                    "Apply only warranted, exact generator edits in a distinct version.",
                    "Dispatch Blender via Actions; compare new images and GLB evidence.",
                    "No-op runs are not visual progress; user owns artistic approval."
                ]}
    images = {}
    for asset in ASSETS:
        if asset not in entries:
            manifest["asset_candidates"][asset] = {"status": "no_successful_run"}
            continue
        entry = entries[asset]
        try:
            folder, paths = find_four_views(asset, entry["branch"])
            entry["preview_directory"] = folder
            entry["view_paths"] = paths
            entry["status"] = "review_ready" if len(paths) == 4 else "missing_four_views"
            if paths and not args.check_only:
                for view, path in paths.items():
                    raw = read_blob(entry["branch"], path)
                    if raw:
                        images[(asset, view)] = raw
                    else:
                        entry["status"] = "incomplete_image_download"
            manifest["asset_candidates"][asset] = entry
        except Exception as exc:
            entry["status"] = "inspection_error"
            entry["error"] = str(exc)[:200]
            manifest["asset_candidates"][asset] = entry
    # Always publish a contact sheet, including explicit failure placeholders.
    # The former conditional silently omitted the JPG when API/image access failed,
    # making the subsequent git add fail and hiding the actual review problem.
    from PIL import Image, ImageDraw, ImageOps
    width, height = 430, 445
    board = Image.new("RGB", (width * len(VIEWS), height * len(ASSETS)), "#1d1d1d")
    drawing = ImageDraw.Draw(board)
    for row, asset in enumerate(ASSETS):
        entry = manifest["asset_candidates"][asset]
        for col, view in enumerate(VIEWS):
            left, top = col * width, row * height
            raw = images.get((asset, view))
            if raw:
                try:
                    with Image.open(io.BytesIO(raw)) as im:
                        thumbnail = ImageOps.contain(im.convert("RGB"), (width - 16, height - 42))
                        board.paste(thumbnail, (left + (width - thumbnail.width)//2, top + 28))
                except Exception as exc:
                    entry["status"] = "invalid_render_image"
                    entry.setdefault("image_errors", {})[view] = str(exc)[:180]
            else:
                drawing.text((left + 12, top + 48), "MISSING RENDER / NOT REVIEWED", fill="#ff9d85")
                drawing.text((left + 12, top + 72), entry["status"][:50], fill="#ff9d85")
            drawing.text((left + 12, top + 9), asset.upper() + " - " + view, fill="#f0e9d9")
    board.save(OUTPUT / "latest_contact_sheet.jpg", quality=85, optimize=True)
    manifest["images_downloaded"] = len(images)
    manifest["all_assets_review_ready"] = (
        len(images) == len(ASSETS) * len(VIEWS)
        and all(e["status"] == "review_ready" for e in manifest["asset_candidates"].values())
    )
    manifest["art_review_completed"] = False
    (OUTPUT / "latest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for asset, entry in manifest["asset_candidates"].items():
        print(asset, entry["status"], entry.get("branch", ""))
    print("REVIEW_PACKET_READY", str(OUTPUT / "latest.json"),
          "IMAGE_COUNT", len(images), "AI_REVIEW_REQUIRED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
