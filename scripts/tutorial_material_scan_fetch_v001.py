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
            if min(pic.width,pic.height)<512:raise RuntimeError(f'Scan resolution too small {asset}/{channel}')
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

if config['kind']=='wood':
    # Derived endgrain maps are procedural art based on photographed CC0 wood scans.
    import numpy as np,shutil
    scan=np.asarray(Image.open(root/'wood_albedo.jpg').convert('RGB'),dtype=np.float32)
    H,W=scan.shape[:2]
    yy,xx=np.mgrid[:H,:W].astype(np.float32)
    U=xx/max(1,W-1);V=yy/max(1,H-1)
    wave=np.sin(U*155+1.8*np.sin(V*9)+.6*np.sin(V*22))
    fine=np.sin(U*370+.8*np.sin(V*17))
    fibre_dark=np.clip(.48+.37*wave+.15*fine,0,1)
    irregular=np.sin(V*14.7+U*19)
    split_color=np.clip(scan*(.60+.23*fibre_dark[...,None])+
                        np.asarray([19,13,7])*np.clip(irregular[...,None],0,1),0,255).astype('uint8')
    Image.fromarray(split_color,'RGB').save(root/'split_albedo.jpg',quality=93,subsampling=0,optimize=True)
    x=U-.5;y=V-.5
    radius=np.sqrt(x*x+y*y)
    angle=np.arctan2(y,x)
    distorted=radius+.009*np.sin(7*angle+radius*10)+.004*np.sin(11*angle-radius*22)
    ring_phase=2*np.pi*distorted*43
    early_late=np.clip(.61+.24*np.cos(ring_phase)+.10*np.cos(2*ring_phase),.30,.94)
    radial_checks=np.minimum(abs(np.arctan2(np.sin(angle+.27),np.cos(angle+.27))),
                             abs(np.arctan2(np.sin(angle-.87),np.cos(angle-.87))))
    crack_dark=np.where((radial_checks<.020)&(radius>.075)&(radius<.45),.36,1.0)
    base=np.asarray([165,113,69] if config['species']=='roble' else [182,157,120],dtype=np.float32)
    end=(base[None,None,:]*(early_late*crack_dark)[...,None] + .18*scan).clip(0,255).astype('uint8')
    Image.fromarray(end,'RGB').save(root/'endgrain_albedo.jpg',quality=93,subsampling=0,optimize=True)
    for role in ('split','endgrain'):
        shutil.copyfile(root/'wood_normal.png',root/(role+'_normal.png'))
        shutil.copyfile(root/'wood_roughness.png',root/(role+'_roughness.png'))
    manifest_note='Real CC0 wood/bark photos; longitudinal fracture/endgrain ALBEDO maps are anatomically derived, NOT independent scans'
else:manifest_note='Actual CC0 photographed surface scan'

manifest={
 'slug':slug,'asset_name':config['name'],'license':'CC0 (Poly Haven)',
 'derived_anatomical_maps':manifest_note,'photographic_scans':receipts,'product_photo_references':'anatomy-only; not downloaded or republished',
 'scope':'2D material scans; the complete 3D shape is artist-modeled, NOT a 3D scan',
 'reference_links':config['references']
}
(root/'provenance.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print('CC0_SCAN_READY',json.dumps({'slug':slug,'files':len(receipts),'bytes':sum(x['size'] for x in receipts)}))
