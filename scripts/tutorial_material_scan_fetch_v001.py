#!/usr/bin/env python3
"""Fetch only Poly Haven CC0 photographic PBR source maps for the selected
Project Genesis tutorial material. No third-party retail photo is redistributed.
Keep exact URLs, source bytes, attribution and hashes.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from PIL import Image
import io,json,hashlib,sys

slug=sys.argv[1]
config=json.loads(Path(f'production/tutorial_materials/config/{slug}.json').read_text())
root=Path(f'production/tutorial_materials/generated/{slug}/source')
root.mkdir(parents=True,exist_ok=True)
receipts=[]
for role,asset in config['scans'].items():
    req=Request(f'https://api.polyhaven.com/files/{asset}',headers={'User-Agent':'ProjectGenesis-CC0-MaterialAssets/1.0'})
    with urlopen(req,timeout=60) as rsp: manifest=json.load(rsp)
    for channel,aliases in [
        ('albedo',('Diffuse','diffuse','diff','albedo','Col','Color','col')),
        ('normal',('nor_gl','normal_gl','NormalGL','normal')),
        ('roughness',('Rough','rough','Roughness','roughness'))
    ]:
        name=next((k for k in aliases if k in manifest),None)
        if name is None:raise RuntimeError(f'{asset} lacks required {channel} photographic PBR map; refusing synthetic fake')
        versions=manifest[name]
        info=None
        for resolution in ('2k','1k','4k'):
            if resolution in versions:
                for ext in ('jpg','png'):
                    entry=versions[resolution].get(ext)
                    if isinstance(entry,dict) and entry.get('url'):info=entry;break
            if info:break
        if not info:raise RuntimeError(f'{asset} lacks JPEG/PNG for {channel}')
        url=info['url']
        with urlopen(Request(url,headers={'User-Agent':'ProjectGenesis-CC0-Texture/1.0'}),timeout=120) as rsp:raw=rsp.read()
        if not 10000<len(raw)<30000000:raise RuntimeError(f'PBR map corrupted/budget exceeded {asset}/{channel}')
        with Image.open(io.BytesIO(raw)) as original:
            pic=original.convert('RGB' if channel!='roughness' else 'L')
            pic.thumbnail((1536,1536),Image.Resampling.LANCZOS)
            if pic.width!=pic.height:raise RuntimeError(f'Unusual non-square scan map {asset}/{channel}')
            target=root/f'{role}_{channel}.png'
            if channel=='albedo':
                target=target.with_suffix('.jpg')
                pic.save(target,format='JPEG',quality=92,subsampling=0,optimize=True)
            else:
                pic.save(target,optimize=True)
        receipts.append({'role':role,'asset':asset,'channel':channel,'source_url':url,
            'page':f'https://polyhaven.com/a/{asset}','license':'CC0',
            'download_sha256':hashlib.sha256(raw).hexdigest(),
            'converted_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'path':str(target),'size':target.stat().st_size,'dimensions':list(pic.size)})
manifest={
 'slug':slug,'asset_name':config['name'],'license':'CC0 (Poly Haven)',
 'photographic_scans':receipts,'product_photo_references':'anatomy-only; not downloaded or republished',
 'scope':'2D material scans; the complete 3D shape is artist-modeled, NOT a 3D scan',
 'reference_links':config['references']
}
(root/'provenance.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print('CC0_SCAN_READY',json.dumps({'slug':slug,'files':len(receipts),'bytes':sum(x['size'] for x in receipts)}))
