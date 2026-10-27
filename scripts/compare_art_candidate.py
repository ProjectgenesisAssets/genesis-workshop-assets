#!/usr/bin/env python3
"""Compare actual GitHub Actions Blender renders without inventing art scores.

Keeps review PNGs small and produces a machine-readable, per-asset receipt.
The objective tests can reject a broken render, but cannot certify an 8/10 asset.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat

VIEWS = {
    "door": ("front", "three_quarter", "side", "rear"),
    "anvil": ("front", "three_quarter", "rear", "detail"),
    "forge": ("front", "three_quarter", "rear", "detail"),
    "bellows": ("front", "three_quarter", "rear", "detail"),
}
CHECKS = {
    "door": ["hinges, handle and latch connected to solid leaf",
             "no floating plate or ornaments", "forged metal reads under neutral lighting"],
    "anvil": ["working face clear and hardened", "horn/heel/stump functional",
              "forged iron not randomly blotchy"],
    "forge": ["front funnel plate catches smoke while firebox stays open",
              "rear brick joints no longer show bright empty gaps",
              "embers glow within charcoal cracks; no detached light spheres"],
    "bellows": ["leather gusset has volumetric functional folds",
                "upper/lower boards and handles are independently functional",
                "grain follows timber, period-appropriate rivets and stitching"],
}


def load(path):
    with Image.open(path) as im:
        if im.width < 600 or im.height < 600:
            raise ValueError(f"Render too small: {path} {im.size}")
        return im.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)


def metrics(im):
    grey = im.convert("L")
    hist = grey.histogram()
    total = sum(hist)
    return {
        "mean_luma": round(ImageStat.Stat(grey).mean[0] / 255, 5),
        "near_black_fraction": round(sum(hist[:6]) / total, 5),
        "near_white_fraction": round(sum(hist[250:]) / total, 5),
        "edge_energy": round(ImageStat.Stat(grey.filter(ImageFilter.FIND_EDGES)).mean[0] / 255, 5),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--asset", choices=VIEWS, required=True)
    p.add_argument("--baseline", required=True, type=Path)
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--baseline-version", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--source-sha", default="unknown")
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    entries = []
    defects = []
    for view in VIEWS[a.asset]:
        old = load(a.baseline / f"{view}.png")
        new = load(a.candidate / f"{view}.png")
        before, after = metrics(old), metrics(new)
        diff = ImageChops.difference(old, new)
        difference = round(sum(ImageStat.Stat(diff).mean) / (255 * 3), 5)
        if after["near_white_fraction"] > .65:
            defects.append(f"{view}: OVEREXPOSURE")
        if after["near_black_fraction"] > .85:
            defects.append(f"{view}: UNDEREXPOSURE")
        if after["edge_energy"] < .008:
            defects.append(f"{view}: LOW_DETAIL")
        sheet = Image.new("RGB", (1024, 512), (25, 25, 25))
        sheet.paste(old, (0, 0))
        sheet.paste(new, (512, 0))
        sheet.save(a.out / f"compare_{view}.png", optimize=True)
        entries.append({"view": view, "baseline": before, "candidate": after,
                        "mean_absolute_rgb_change": difference})

    changed = any(e["mean_absolute_rgb_change"] > .005 for e in entries)
    if not changed:
        defects.append("NO_MEASURABLE_RENDER_CHANGE")
    report = {
        "asset": a.asset, "baseline_version": a.baseline_version,
        "candidate_version": a.version, "source_sha": a.source_sha,
        "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "comparison": entries, "objective_defects": defects,
        "technical_visual_gate": "pass" if not defects else "fail",
        "artistic_score": None, "artist_approved": False,
        "approval_status": "CANDIDATE_NEEDS_HUMAN_REVIEW",
        "best_candidate_changed": False,
        "art_review_checklist": CHECKS[a.asset],
        "note": "Pixel differences are evidence of a change, NOT proof of artistic improvement.",
    }
    (a.out / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [f"# {a.asset}: {a.baseline_version} vs {a.version}", "",
             f"Render change observed: **{'yes' if changed else 'no'}**.",
             f"Objective QA: **{report['technical_visual_gate']}**.",
             "Artistic review: **not approved / no invented numeric score**.", "",
             "| View | RGB delta | Base luma | New luma |", "|---|---:|---:|---:|"]
    for e in entries:
        lines.append(f"| {e['view']} | {e['mean_absolute_rgb_change']:.3f} | "
                     f"{e['baseline']['mean_luma']:.3f} | {e['candidate']['mean_luma']:.3f} |")
    lines += ["", "## Manual physical/art review", ""]
    lines += [f"- [ ] {item}" for item in CHECKS[a.asset]]
    (a.out / "comparison.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if not changed:
        raise SystemExit("Candidate is visually identical to baseline; refusing relaunch credit")


if __name__ == "__main__":
    main()
