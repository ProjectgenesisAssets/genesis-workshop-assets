#!/usr/bin/env python3
"""Add real CC0 bark/spool photographic PBR to V006 without replacing core material identity."""
import os,json,hashlib,urllib.request,time,pathlib
K=os.environ.get("ASSET_KIND","").removeprefix("asset/")
choice={
 "dry-oak-wood":("jolcham_oak_bark_01","bark"),
 "dry-ash-wood":("bark_brown_01","bark"),
 "linen-thread":("ash_veneer","bobbin")
}
if K not in choice:
 print("No secondary scan required for "+K)
 raise SystemExit(0)
asset,role=choice[K]
root=pathlib.Path("sources")/K
root.mkdir(parents=True,exist_ok=True)
def get(url):
 for k in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"ProjectGenesis-CC0-CreativeTools/1.0 Powered by Poly Haven"}),timeout=90) as f:return f.read()
  except Exception:
   if k==2:raise
   time.sleep((k+1)*4)
tree=json.loads(get("https://api.polyhaven.com/files/"+asset))
mapkeys={"Color":["Diffuse","Coll1"],"Roughness":["Rough"],"NormalGL":["nor_gl"]}
outputs={}
for label,names in mapkeys.items():
 layer=next((tree[x] for x in names if x in tree),None)
 if not layer:raise RuntimeError("Missing "+label+" for "+asset)
 selection=None
 for res in ["2k","4k"]:
  for ext in (["png","jpg"] if label=="NormalGL" else ["jpg","png"]):
   v=layer.get(res,{}).get(ext)
   if isinstance(v,dict) and v.get("url"):
    selection=(v["url"],ext,res,v.get("md5"));break
  if selection:break
 if not selection:raise RuntimeError("No "+label+" file found in 2K/4K")
 url,ext,res,md5=selection
 raw=get(url)
 if md5 and hashlib.md5(raw).hexdigest().lower()!=md5.lower():raise RuntimeError("MD5 mismatch")
 outputs[label]={"bytes":raw,"url":url,"format":ext,"resolution":res,"sha256":hashlib.sha256(raw).hexdigest()}
for label,v in outputs.items():
 (root/("zz_v006_"+role+"_"+label+"."+v["format"])).write_bytes(v["bytes"])
(root/("secondary_sources.json")).write_text(json.dumps({
 "source_url":"https://polyhaven.com/a/"+asset,
 "license":"CC0-1.0","credit":"Powered by Poly Haven",
 "role":role,
 "maps":{k:{kk:vv for kk,vv in x.items() if kk!="bytes"} for k,x in outputs.items()},
 "biological_species_claim":False if role=="bobbin" else (K=="dry-oak-wood")
},indent=2))
print(json.dumps({"secondary":"ready","asset":K,"role":role,"source":asset,"bytes":sum(len(v["bytes"]) for v in outputs.values())}))
