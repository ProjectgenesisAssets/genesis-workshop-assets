# Download real CC0 PBR maps via requests before Blender, avoiding urllib 403.
from pathlib import Path
import requests,hashlib,json
out=Path('output_charcoal_v007_photoscan');out.mkdir(exist_ok=True)
src='https://api.polyhaven.com/files/dead_tree_trunk_02'
d=requests.get(src,timeout=40,headers={'User-Agent':'ProjectGenesis3DAssetProduction/1.0'});d.raise_for_status()
payload=d.json()
maps=[
 ('Diffuse','jpg','original_realwood_scan_color_2k.jpg'),
 ('nor_gl','png','original_realwood_scan_normal_2k.png'),
 ('Rough','png','original_realwood_scan_roughness_2k.png')
]
for group,ext,name in maps:
 meta=payload[group]['2k'][ext];url=meta['url']
 if not url.startswith('https://dl.polyhaven.org/'):raise RuntimeError('untrusted scan host')
 res=requests.get(url,timeout=100,headers={'User-Agent':'ProjectGenesis3DAssetProduction/1.0'});res.raise_for_status()
 p=out/name;p.write_bytes(res.content)
 if len(res.content)<4096:raise RuntimeError('invalid texture '+name)
 print(name,'bytes',len(res.content),'sha256',hashlib.sha256(res.content).hexdigest())
