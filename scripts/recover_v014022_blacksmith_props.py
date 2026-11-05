#!/usr/bin/env python3
"""V014022 experimental blacksmith recovery, preserving approved originals.
Download the EXACT Quaternius Standard Anvil_Log.gltf and its relative buffers/textures
from a publicly readable archival mirror of the CC0 Standard kit.
Download ONE small CC0 candidate bellows (not user-approved) from 3DAssets.dev.
Inspect real bytes and glTF internal data, record SHA256 and provenance.
Never touch approved production models or main game.
"""
from __future__ import annotations
import hashlib, json, os, pathlib, struct, time, urllib.parse, urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path("production/game_v014022/herrero_recovery/v001")
ANVIL = ROOT / "anvil_quaternius_cc0_original"
BELLOWS = ROOT / "bellows_cc0_candidate"
SOURCE_BASE = ("https://raw.githubusercontent.com/RTheoGH/Projet_VR/main/"
               "Assets/Packs/fantasyprops/")
SOURCE_PAGE = "https://quaternius.com/packs/fantasypropsmegakit"
BELLOWS_URL = "https://cdn.3dassets.dev/assets/37560/v1/model.glb"
BELLOWS_PAGE = ("https://3dassets.dev/assets/"
                "blacksmith-forge-and-armoury-blacksmith-forge-and-armo-2c5ef7d9")
AGENT = "ProjectGenesis-CC0-asset-recovery/1.0"
TIMEOUT = 90

def sha256(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()

def download(url: str, target: pathlib.Path, *, limit: int=22_000_000) -> bytes:
    target.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(1, 5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as reply:
                if reply.status != 200: raise ValueError(f"HTTP {reply.status}")
                data = reply.read(limit + 1)
                if len(data) > limit: raise ValueError("oversized source: " + str(len(data)))
                if len(data) < 48: raise ValueError("unexpectedly small source")
                target.write_bytes(data)
                print(f"DOWNLOADED {target} {len(data)} bytes SHA256={sha256(data)}", flush=True)
                return data
        except Exception as e:
            last = e
            print(f"RETRY {attempt}/4 {url} -> {e}", flush=True)
            time.sleep(min(3 * attempt, 10))
    raise RuntimeError(f"Unable to retrieve {url}: {last}")

def is_png(b: bytes) -> bool:
    return b[:8] == b"\x89PNG\r\n\x1a\n"

def validate_glb(b: bytes) -> dict:
    if b[:4] != b"glTF" or len(b) < 28: raise ValueError("not a GLB 2")
    version, size = struct.unpack_from("<II", b, 4)
    if version != 2 or size != len(b): raise ValueError("bad GLB header or truncated")
    chunklen, chunkfmt = struct.unpack_from("<II", b, 12)
    if chunkfmt != 0x4e4f534a: raise ValueError("first chunk is not JSON")
    scene = json.loads(b[20:20 + chunklen].decode("utf-8"))
    if scene.get("asset", {}).get("version") != "2.0" or not scene.get("meshes"):
        raise ValueError("GLB missing valid glTF 2.0 mesh")
    # Ensure buffer payload is inside the actual file.
    if len(b) < 28 + chunklen: raise ValueError("GLB no binary chunk")
    return {"meshes": len(scene.get("meshes", [])),
            "nodes": len(scene.get("nodes", [])),
            "materials": len(scene.get("materials", [])),
            "animations": len(scene.get("animations", [])),
            "extensionsUsed": scene.get("extensionsUsed", []),
            "extensionsRequired": scene.get("extensionsRequired", []),
            "version": scene["asset"]["version"]}

def main() -> None:
    urls = {}
    anvil_url = SOURCE_BASE + "Anvil_Log.gltf"
    anvil_json_bytes = download(anvil_url, ANVIL / "Anvil_Log.gltf")
    scene = json.loads(anvil_json_bytes)
    assert scene["asset"]["version"] == "2.0"
    assert scene.get("meshes"), "anvil missing meshes"
    targets = scene.get("buffers", []) + scene.get("images", [])
    seen = set()
    for target in targets:
        name = target.get("uri")
        if not name or name.startswith(("data:", "http:", "https:")): continue
        if "/" in name or ".." in name: raise ValueError("unsafe resource URI: " + name)
        if name in seen: continue
        seen.add(name)
        url = SOURCE_BASE + urllib.parse.quote(name, safe="")
        b = download(url, ANVIL / name)
        if name.lower().endswith(".png") and not is_png(b):
            raise ValueError("texture not a real PNG: " + name)
        if name.lower().endswith(".bin"):
            expected = target.get("byteLength")
            if isinstance(expected, int) and len(b) != expected:
                raise ValueError(f"{name}: expected {expected} bytes but got {len(b)}")
        urls[str(ANVIL / name)] = url
    urls[str(ANVIL / "Anvil_Log.gltf")] = anvil_url
    glb = download(BELLOWS_URL, BELLOWS / "Bellows.glb")
    glb_meta = validate_glb(glb)
    urls[str(BELLOWS / "Bellows.glb")] = BELLOWS_URL

    files = [{"path": x, "bytes": os.path.getsize(x),
              "sha256": sha256(pathlib.Path(x).read_bytes()), "source": u}
             for x, u in sorted(urls.items())]
    manifest = {
        "status": "EXPERIMENTAL_NOT_APPROVED",
        "purpose": "Unblock V014022 and run real Playwright Ordan tutorial",
        "createdAtUtc": datetime.now(timezone.utc).isoformat(),
        "policy": {"userVisualApproval": False, "noMainModification": True,
                   "anvil": "Quaternius original CC0", "bellows": "CC0 fallback candidate"},
        "anvil": {"license": "CC0 1.0", "creator": "Quaternius",
                  "originalPack": SOURCE_PAGE,
                  "archivalMirrorRepo": "RTheoGH/Projet_VR",
                  "originalGLTF": str(ANVIL / "Anvil_Log.gltf"),
                  "meshCount": len(scene["meshes"]),
                  "relativeImages": [x["uri"] for x in scene.get("images", []) if "uri" in x],
                  "relativeBuffers": [x["uri"] for x in scene.get("buffers", []) if "uri" in x]},
        "bellows": {"license": "CC0 1.0", "creator": "3DAssets.dev", "source": BELLOWS_PAGE,
                    "GLB": str(BELLOWS / "Bellows.glb"), "metadata": glb_meta,
                    "licenseCaveat": "Source declares CC0. Candidate not visually approved"},
        "totalBytes": sum(x["bytes"] for x in files),
        "files": files,
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "recovery_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("PASS V014022_RECOVERY_REAL_BYTES",
          json.dumps({"files": len(files), "totalBytes": manifest["totalBytes"],
                      "bellows": glb_meta}, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
