#!/usr/bin/env python3
"""Project Genesis: auditable acquisition of CC0 scan-derived PBR textures."""
import hashlib, io, json, os, pathlib, re, sys, time, urllib.parse, urllib.request, zipfile
K=os.environ.get("ASSET_KIND","").removeprefix("asset/")
CONFIG={
 "dry-oak-wood":(["oak","wood"],["oak","wood","rough"],["floor","tile","parquet","painted"]),
 "dry-ash-wood":(["ash","wood"],["ash","wood","raw"],["floor","tile","parquet","painted"]),
 "tanned-cowhide":(["leather"],["leather","brown","natural","grain"],["perforated","crocodile","synthetic","tufted"]),
 "tanned-goatskin":(["leather"],["leather","soft","fine","natural"],["perforated","crocodile","synthetic","tufted"]),
 "hemp-cord":(["rope"],["rope","fiber","natural"],["metal","synthetic","plastic"]),
 "linen-thread":(["linen","fabric"],["linen","weave","natural"],["denim","velvet","polyester","synthetic"]),
}
if K not in CONFIG:raise SystemExit("Unsupported material: "+K)
queries,good,bad=CONFIG[K]
root=pathlib.Path("sources")/K
root.mkdir(parents=True,exist_ok=True)
HEADER={"User-Agent":"ProjectGenesis-CC0-asset-pipeline/1.0 (educational, provenance-preserving)"}
def request(url):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=HEADER),timeout=75) as res:
    return res.read()
  except Exception:
   if attempt==2:raise
   time.sleep((attempt+1)*3)
def candidates():
 seen={}
 for q in queries:
  url="https://ambientcg.com/api/v3/assets?"+urllib.parse.urlencode({"type":"material","q":q,"limit":75,"include":"title,tags,downloads"})
  result=json.loads(request(url))
  for asset in result.get("assets",[]):
   if asset.get("id"):seen[asset["id"]]=asset
 return list(seen.values())
def word(txt,token):return bool(re.search(r"\b"+re.escape(token)+r"\b",txt))
def rank(a):
 txt=(a.get("title","")+" "+str(a.get("tags") or "")).lower()
 return sum(12 if word(txt,x) else 0 for x in good)-sum(15 if word(txt,x) else 0 for x in bad)
def package(a):
 dl=a.get("downloads") or []
 for fmt in ("4K-PNG","4K-JPG","2K-PNG","2K-JPG"):
  opts=[p for p in dl if p.get("attributes")==fmt and p.get("url")]
  if opts:return opts[0],fmt
 return None,None
catalog=sorted(candidates(),key=lambda a:rank(a),reverse=True)
eligible=[a for a in catalog if package(a)[0]]
if not eligible:raise RuntimeError("No CC0 candidate with 2K/4K PBR download for "+K)
shortlist=[{"id":a["id"],"title":a.get("title"),"score":rank(a),"package":package(a)[1],"url":"https://ambientcg.com/a/"+a["id"]} for a in eligible[:12]]
(root/"candidates.json").write_text(json.dumps(shortlist,indent=2),encoding="utf-8")
# Use source image sets as surface references only. Their species/fiber identity is not automatically certified.
failure=[]
for a in eligible[:6]:
 pkg,fmt=package(a)
 try:
  raw=request(pkg["url"])
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   items=[i for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith((".png",".jpg",".jpeg"))]
   def match(tag):
    return any(tag in pathlib.PurePosixPath(i.filename).name.lower() for i in items)
   if not (match("color") or match("albedo") or match("diffuse")) or not match("roughness") or not match("normalgl"):
    raise ValueError("Missing Color/Roughness/NormalGL maps")
   if any(i.file_size>200*1024*1024 for i in items):
    raise ValueError("oversized texture")
   for i in items:
    dst=root/pathlib.PurePosixPath(i.filename).name
    dst.write_bytes(z.read(i))
  (root/"source.zip").write_bytes(raw)
  txt=(a.get("title","")+" "+str(a.get("tags") or "")).lower()
  species_word={"dry-oak-wood":"oak","dry-ash-wood":"ash","tanned-cowhide":"cow","tanned-goatskin":"goat","hemp-cord":"hemp","linen-thread":"linen"}[K]
  manifest={
   "asset":K,"id":a["id"],"title":a.get("title"),"source_url":"https://ambientcg.com/a/"+a["id"],
   "download_url":pkg["url"],"source_package":fmt,"license":"CC0-1.0",
   "sha256":hashlib.sha256(raw).hexdigest(),"scan_technique_confirmed":False,
   "species_or_fiber_verified":word(txt,species_word),
   "visual_approval":False,
   "caution":"A CC0 PBR texture is not necessarily a photogrammetric scan or proof of a biological species.",
   "shortlist":shortlist,
  }
  (root/"provenance.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
  print(json.dumps({"result":"downloaded","asset":K,"id":a["id"],"package":fmt,"bytes":len(raw),"species_or_fiber_verified":manifest["species_or_fiber_verified"]}))
  break
 except Exception as e:failure.append({"id":a.get("id"),"error":str(e)})
else:
 (root/"download_failures.json").write_text(json.dumps(failure,indent=2),encoding="utf-8")
 raise RuntimeError("No complete compatible PBR package retrieved: "+str(failure))
