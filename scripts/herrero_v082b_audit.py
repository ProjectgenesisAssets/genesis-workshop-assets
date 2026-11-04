#!/usr/bin/env python3
"""Read-only inventory of the approved 15.9MB blacksmith V082-B GLB.
Do not make geometric, texture, material or color assumptions before this audit.
Produces deterministic JSON + Markdown for the following optimization candidate.
"""
import argparse,hashlib,json,struct,collections,os
from pathlib import Path

def png_size(blob):
 if blob[:8]==b'\x89PNG\r\n\x1a\n' and len(blob)>=24:
  w,h=struct.unpack('>II',blob[16:24]);return w,h
 return None
def jpeg_size(blob):
 p=2
 if blob[:2]!=b'\xff\xd8':return None
 while p+9<len(blob):
  if blob[p]!=255:p+=1;continue
  marker=blob[p+1];p+=2
  if marker in (0xd8,0xd9,0x01):continue
  if p+2>len(blob):break
  n=struct.unpack('>H',blob[p:p+2])[0]
  if marker in (0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb):
   return struct.unpack('>HH',blob[p+3:p+7])[::-1]
  p+=max(2,n)
 return None
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('input',type=Path)
 ap.add_argument('--out',type=Path,default=Path('reports/herrero_v082b_lossless_baseline'))
 opts=ap.parse_args()
 d=opts.input.read_bytes()
 assert d[:4]==b'glTF' and int.from_bytes(d[4:8],'little')==2
 assert int.from_bytes(d[8:12],'little')==len(d)
 p=12;js=None;binchunk=None;chunks=[]
 while p<len(d):
  size,kind=struct.unpack_from('<I4s',d,p);p+=8
  raw=d[p:p+size];p+=size;chunks.append(dict(kind=kind.decode(),bytes=size))
  if kind==b'JSON':js=json.loads(raw)
  if kind==b'BIN\0':binchunk=raw
 assert js and binchunk is not None
 buffers=js.get('bufferViews',[]);images=js.get('images',[])
 materials=js.get('materials',[]);textures=js.get('textures',[])
 refs=collections.Counter()
 def explore(v):
  if isinstance(v,dict):
   for k,item in v.items():
    if k in ('index',) and item is not None and isinstance(item,int):
     pass
    if k in ('baseColorTexture','metallicRoughnessTexture','normalTexture','occlusionTexture','emissiveTexture','diffuseTexture','specularGlossinessTexture','clearcoatTexture','clearcoatRoughnessTexture','clearcoatNormalTexture','sheenColorTexture','sheenRoughnessTexture','transmissionTexture','thicknessTexture') and isinstance(item,dict) and 'index' in item:
     refs[item['index']]+=1
    explore(item)
  elif isinstance(v,list):
   for item in v:explore(item)
 for mat in materials:explore(mat)
 used_img=collections.Counter()
 for tidx,uses in refs.items():
  if tidx<len(textures):
   ix=textures[tidx].get('source')
   if ix is not None:used_img[ix]+=uses
 image_rows=[]
 for i,img in enumerate(images):
  view=buffers[img['bufferView']] if 'bufferView' in img else None
  imgbytes=binchunk[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']] if view else b''
  image_rows.append(dict(index=i,name=img.get('name'),mime=img.get('mimeType'),bytes=len(imgbytes),
   share_pct=round(100*len(imgbytes)/len(d),2),dimensions=png_size(imgbytes) or jpeg_size(imgbytes),
   sha256=hashlib.sha256(imgbytes).hexdigest() if imgbytes else None,
   uses=int(used_img[i]),view=img.get('bufferView')))
 dup=collections.defaultdict(list)
 for x in image_rows:
  if x['sha256']:dup[x['sha256']].append(x['index'])
 mesh_rows=[]
 triangles=0
 for mi,m in enumerate(js.get('meshes',[])):
  for pi,prim in enumerate(m.get('primitives',[])):
   ac=js.get('accessors',[])
   indices=ac[prim['indices']]['count'] if 'indices' in prim else 0
   positions=ac[prim['attributes']['POSITION']]['count']
   tris=indices//3 if prim.get('mode',4)==4 and indices else max(0,positions//3)
   triangles+=tris
   mesh_rows.append(dict(mesh=mi,mesh_name=m.get('name'),primitive=pi,vertices=positions,
      indices=indices,triangles=tris,material=prim.get('material'),attribute_count=len(prim['attributes'])))
 other_views=collections.Counter()
 image_view_ids=set(x.get('bufferView') for x in images)
 for i,view in enumerate(buffers):
  if i not in image_view_ids:other_views['bytes']+=view['byteLength']
 info=dict(file=opts.input.name,bytes=len(d),mb=round(len(d)/1000000,3),mib=round(len(d)/1048576,3),
  sha256=hashlib.sha256(d).hexdigest(),git_blob_sha1=hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest(),
  chunks=chunks,nodes=len(js.get('nodes',[])),meshes=len(js.get('meshes',[])),mesh_primitives=len(mesh_rows),
  triangles=triangles,materials=len(materials),textures=len(textures),images=len(images),
  image_total_bytes=sum(x['bytes'] for x in image_rows),
  images_pct=round(100*sum(x['bytes'] for x in image_rows)/len(d),2),
  buffer_geometry_views_bytes=other_views['bytes'],images_detail=sorted(image_rows,key=lambda x:x['bytes'],reverse=True),
  duplicates=[group for group in dup.values() if len(group)>1],
  unused_images=[x['index'] for x in image_rows if not x['uses']],
  unused_textures=[i for i in range(len(textures)) if not refs[i]],
  extensions=js.get('extensionsUsed',[]),extensionsRequired=js.get('extensionsRequired',[]),
  mesh_primitives_detail=mesh_rows,
  quality_policy=dict(max_allowed_visible_loss_pct=2.5,target_visible_loss_pct=1.5,
    unchanged_geometry=True,original_approval_retained=True,optimized_candidate_requires_human_approval=True))
 assert len(d)==15887816, f'Unexpected source byte count: {len(d)}'
 assert info['git_blob_sha1']=='eef69d28dd8d53b5934442279a8b027bdfbfa157', 'Changed master; stop'
 opts.out.mkdir(parents=True,exist_ok=True)
 (opts.out/'baseline.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
 lines=[
 '# Herrero V082-B · baseline read-only',
 f'- GLB original: {len(d):,} bytes ({info["mib"]} MiB)',
 f'- Verificado Git blob: `{info["git_blob_sha1"]}`',
 f'- Mallas: {info["meshes"]} · triángulos: {info["triangles"]:,} · materiales: {len(materials)}',
 f'- Texturas: {len(textures)} · imágenes: {len(images)} · bytes de imágenes: {info["image_total_bytes"]:,} ({info["images_pct"]} % del GLB)',
 f'- Views de geometría: {other_views["bytes"]:,} bytes; duplicados binarios: {info["duplicates"]}',
 f'- Imágenes no usadas: {info["unused_images"]} · texturas no usadas: {info["unused_textures"]}',
 '',
 '## Texturas por tamaño',
 '| Índice | Tamaño bytes | Resolución | Formato | Usos |',
 '|---|---:|---|---|---:|'
 ]
 for x in info['images_detail']:
  lines.append(f'| {x["index"]} | {x["bytes"]:,} | {x["dimensions"]} | {x["mime"]} | {x["uses"]} |')
 lines+=['','**Regla:** no aprobar ni integrar una optimización con pérdida visual superior al 2,5 %. Antes de reducir texturas/triángulos, probar limpieza y compresión sin pérdida. Las mediciones cuantitativas no sustituyen aprobación visual.']
 (opts.out/'baseline.md').write_text('\n'.join(lines)+'\n')
 print('BASELINE AUDIT OK',json.dumps({k:v for k,v in info.items() if k not in ('images_detail','mesh_primitives_detail')},ensure_ascii=False))
 print('BASELINE IMAGES',json.dumps(info['images_detail'],ensure_ascii=False))
if __name__=='__main__':main()
