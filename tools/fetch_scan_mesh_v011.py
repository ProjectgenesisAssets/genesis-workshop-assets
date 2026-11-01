#!/usr/bin/env python3
"""Download actual Poly Haven CC0 photogrammetric 3D mesh, not just a PBR tile."""
import pathlib,urllib.request,hashlib,json,os,time
K=os.environ["ASSET_KIND"]
scans={"dry-oak-wood":"dead_tree_trunk","dry-ash-wood":"dead_tree_trunk_02"}
if K not in scans:raise SystemExit("This scan experiment is wood only")
asset=scans[K];root=pathlib.Path("sources")/K/"photogrammetry_v011";root.mkdir(parents=True,exist_ok=True)
UA={"User-Agent":"ProjectGenesis CC0 Photogrammetry (Powered by Poly Haven)"}
def get(url):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=110) as f:return f.read()
  except Exception:
   if attempt==2:raise
   time.sleep(3*(attempt+1))
api=json.loads(get("https://api.polyhaven.com/files/"+asset))
selection=api["gltf"]["2k"]["gltf"]
items={asset+"_2k.gltf":selection}
items.update(selection["include"])
files=[]
for filename,desc in items.items():
 name=pathlib.PurePosixPath(filename)
 if ".." in name.parts or name.is_absolute():raise RuntimeError("Unsafe source filename")
 path=root/pathlib.Path(filename);path.parent.mkdir(parents=True,exist_ok=True)
 data=get(desc["url"])
 if desc.get("md5") and hashlib.md5(data).hexdigest().lower()!=desc["md5"].lower():raise RuntimeError("Checksum mismatch "+filename)
 path.write_bytes(data)
 files.append({"path":filename,"size":len(data),"sha256":hashlib.sha256(data).hexdigest(),"url":desc["url"]})
manifest={"candidate":K,"mesh_source":asset,"asset_page":"https://polyhaven.com/a/"+asset,"license":"CC0-1.0","credit":"Powered by Poly Haven","mesh_type":"photogrammetry","species_verified":False,"visual_approved":False,"files":files}
(root/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({"asset":K,"scan":asset,"bytes":sum(x["size"] for x in files)}))
