"""Select a Blender-ready .glb/.blend from the nested Fab download ZIP, safely.

Outputs exactly SOURCE_PATH=<absolute path> for GITHUB_ENV. No asset is
committed or published by this helper.
"""
import argparse
import os
import shutil
import zipfile
from pathlib import Path

MAX_FILES = 15000
MAX_UNCOMPRESSED_BYTES = 1_500_000_000


def safe_unzip(path, target):
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_FILES or sum(info.file_size for info in infos) > MAX_UNCOMPRESSED_BYTES:
            raise RuntimeError("Refusing oversized Fab archive")
        root = target.resolve()
        for item in infos:
            name = item.filename.replace("\\", "/")
            parts = Path(name).parts
            if not parts or name.startswith("/") or any(p in ("..", "") for p in parts):
                raise RuntimeError("Unsafe path in ZIP: " + name)
            dest = (target / name).resolve()
            if not dest.is_relative_to(root):
                raise RuntimeError("ZIP path escapes output")
            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as source, dest.open("wb") as sink:
                    shutil.copyfileobj(source, sink)


def choose_model(payload, directory):
    if payload.suffix.lower() in (".blend", ".glb"):
        return payload
    # The download is often an extensionless file from curl.
    with payload.open("rb") as file:
        signature = file.read(4)
    if signature == b"glTF":
        result = directory / "fab_download.glb"
        shutil.copyfile(payload, result)
        return result
    if signature[:2] != b"PK":
        raise RuntimeError("Expected ZIP or binary GLB; invalid downloaded source")
    safe_unzip(payload, directory / "outer")
    # Nicholas 3D Fab ZIP contains source/More Trees Free.zip with a .blend inside.
    for inner in list(directory.rglob("*.zip")):
        if "nested" in inner.parts:
            continue
        safe_unzip(inner, directory / "nested" / inner.stem)
    glbs = list(directory.rglob("*.glb"))
    blends = list(directory.rglob("*.blend"))
    candidates = glbs if glbs else blends
    if not candidates:
        raise RuntimeError("Fab package does not contain a .glb or .blend model")
    return max(candidates, key=lambda file: file.stat().st_size)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    chosen = choose_model(args.archive.resolve(), args.output_dir.resolve())
    result = str(chosen.resolve())
    if "\n" in result or "\r" in result:
        raise RuntimeError("Unsupported newline in model path")
    print("SOURCE_PATH=" + result)


if __name__ == "__main__":
    main()
