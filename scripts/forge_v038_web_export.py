#!/usr/bin/env python3
"""Convert a Blender GLB with embedded PBR maps into web-sized GLB, preserving mesh data."""
import sys,struct,json,io,hashlib
from pathlib import Path
from PIL import Image
source=Path(sys.argv[1]); target=Path(sys.argv[2]); target.parent.mkdir(parents=True,exist_ok=True)
raw=source.read_bytes()
assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2
n=struct.unpack_from('<I',raw,12)[0]
assert raw[16:20]==b'JSON'
doc=json.loads(raw[20:20+n])
off=20+n
length,tag=struct.unpack_from('<I4s',raw,off)
assert tag==b'BIN\x00'
old=raw[off+8:off+8+length]
image_views={im['bufferView']:im for im in doc['images']}
print('GLB_SOURCE',len(raw),'bufferViews',len(doc['bufferViews']),'images',len(doc['images']),flush=True)
new=bytearray()
for i,view in enumerate(doc['bufferViews']):
    data=old[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
    if i in image_views:
        im=image_views[i]
        img=Image.open(io.BytesIO(data))
        if img.mode=='RGBA':
            assert img.getchannel('A').getextrema()==(255,255)
        if max(img.size)>1536:
            k=1536/max(img.size)
            img=img.resize(tuple(round(v*k) for v in img.size),Image.Resampling.LANCZOS)
        rgb=img.convert('RGB'); output=io.BytesIO()
        is_hot='emissive' in im.get('name','').lower()
        if is_hot:
            rgb.save(output,format='PNG',optimize=True,compress_level=9)
            im['mimeType']='image/png'
        else:
            rgb.save(output,format='JPEG',quality=89 if 'normal' in im.get('name','').lower() else 87,subsampling=0,optimize=True)
            im['mimeType']='image/jpeg'
        data=output.getvalue()
    new.extend(b'\x00'*((-len(new))%4))
    view['byteOffset']=len(new)
    view['byteLength']=len(data)
    new.extend(data)
doc['buffers'][0]['byteLength']=len(new)
j=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode()
j+=b' '*((-len(j))%4)
new.extend(b'\x00'*((-len(new))%4))
res=struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(new))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(new),b'BIN\\x00')+new
target.write_bytes(res)
print('GLB_WEB_HQ',len(res),'sha256',hashlib.sha256(res).hexdigest(),flush=True)
assert 8000000<len(res)<30000000
