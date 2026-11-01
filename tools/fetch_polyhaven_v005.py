#!/usr/bin/env python3
"""Optional selected Poly Haven CC0 PBR replacement for Genesis V005.
Only complete 3-map packs are accepted; never falsely mark a species verified."""
import hashlib,json,os,pathlib,time,urllib.request,urllib.error
K=os.environ.get("ASSET_KIND","").removeprefix("asset/")
CHOICE={
 "dry-ash-wood":("ash_veneer",True),
 "tanned-cowhide":("brown_leather",False),
 "tanned-goatskin":("leather_red_02",False),
}
if K not in CHOICE:
 print("Poly Haven override not specified for "+K+"; original 4K CC0 sources retained.")
 raise SystemExit(0)
asset,species_confirmed=CHOICE[K]
root=pathlib.Path("sources")/K;root.mkdir(parents=True,exist_ok=True)
UA={"User-Agent":"ProjectGenesis-PBR-Pipeline/1.1 (Powered by Poly Haven)"}
def get(url):
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers=UA)
   with urllib.request.urlopen(req,timeout=90) as f:return f.read()
  except Exception:
   if attempt==2:raise
   time.sleep((attempt+1)*3)
def find_layer(payload,key):
 names=[v for v in payload.keys() if v.lower()==key.lower()]
 if key=="Diffuse" and not names:
  names=[v for v in payload if v.lower() in ("coll1","basecolor","color")]
 if not names:raise KeyError("Poly Haven layer not offered: "+key)
 variants=payload[names[0]]
 for res in ("4k","2k","8k"):
  x=variants.get(res, {})
  for fmt in (("png","jpg") if key=="nor_gl" else ("jpg","png")):
   hit=x.get(fmt)
   if isinstance(hit,dict) and hit.get("url"):return hit["url"],fmt,res,hit.get("md5")
 raise ValueError("No suitable image variant for "+key)
pbr=json.loads(get("https://api.polyhaven.com/files/"+asset))
data={}
for layer,filename in (("Diffuse","Color"),("Rough","Roughness"),("nor_gl","NormalGL")):
 url,fmt,res,md5=find_layer(pbr,layer)
 raw=get(url)
 if md5 and hashlib.md5(raw).hexdigest().lower()!=md5.lower():
  raise RuntimeError("Poly Haven integrity mismatch: "+layer)
 data[filename]={"data":raw,"extension":fmt,"resolution":res,"source_url":url,"sha256":hashlib.sha256(raw).hexdigest()}
 # Never save partial 3-map source as if usable.
for name,item in data.items():
 (root/("A000_PolyHaven_"+asset+"_"+name+"."+item["extension"])).write_bytes(item["data"])
manifest={
 "asset":K,"id":"PolyHaven/"+asset,"title":asset.replace("_"," ").title(),
 "source_url":"https://polyhaven.com/a/"+asset,"license":"CC0-1.0",
 "api_credit":"Powered by Poly Haven (https://polyhaven.com)",
 "source_package":"4K independent PBR maps or documented lower available resolution",
 "maps":{name:{k:v for k,v in d.items() if k!="data"} for name,d in data.items()},
 "species_or_fiber_verified":species_confirmed,
 "scan_technique_confirmed":False,
 "visual_approval":False,
 "note":"High-res CC0 PBR photographic surface data; geometry authored in Blender. Leather scan is not a verified animal species."
}
(root/"provenance.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
(root/"candidates.json").write_text(json.dumps([{"id":manifest["id"],"source":manifest["source_url"]}],indent=2))
print(json.dumps({"status":"polyhaven_complete","asset":K,"source":manifest["source_url"],"map_bytes":{x:len(d["data"]) for x,d in data.items()}}))
