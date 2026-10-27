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
    # Repo contents API returns base64 only for ordinary-size review PNGs.
    import base64
    resource = ("/repos/" + REPO + "/contents/" + urllib.parse.quote(path, safe="/")
                + "?ref=" + urllib.parse.quote(branch, safe=""))
    try:
        result = api(resource)
        if result.get("encoding") == "base64" and result.get("content"):
            return base64.b64decode(result["content"])
        # GitHub contents API stops embedding base64 for larger images.
        # Download from the trusted raw.githubusercontent.com URL instead.
        url = result.get("download_url") or ""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
            return None
        token = os.environ.get("GH_TOKEN", "")
        headers = {"User-Agent": "genesis-review-handoff"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=25) as response:
            blob = response.read(12 * 1024 * 1024 + 1)
        return blob if 0 < len(blob) <= 12 * 1024 * 1024 else None
    except (subprocess.CalledProcessError, ValueError, KeyError, OSError, urllib.error.URLError):
        return None

def candidates() -> dict:
    runs = api("/repos/" + REPO + "/actions/runs?per_page=100").get("workflow_runs", [])
    found = {}
    for run in runs:
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        branch = run.get("head_branch") or ""
        if not branch.startswith("production/"):
            continue
        for asset, words in TARGET_NAMES.items():
            if asset in found:
                continue
            if not any(word in branch.lower() for word in words):
                continue
            found[asset] = {"branch": branch, "run_id": run["id"],
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
        views = {slot: f"{prefix}/{source}.png"
                 for slot, source in zip(VIEWS, VIEW_FILES[asset])
                 if f"{prefix}/{source}.png" in files}
        if len(views) == 4:
            matches.append((prefix, views))
    if not matches:
        return None, {}
    # Favor a task-specific auto-preview over inherited baseline images.
    matches.sort(key=lambda pair: ("/production_auto/" in pair[0],
                                    pair[0]))
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
