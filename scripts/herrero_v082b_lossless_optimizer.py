#!/usr/bin/env python3
"""Produce a 100%-pixel-identical GLB candidate using lossless WebP.
Original approval and GLB geometry/PBR are immutable. Candidate stays in CI artifact.
For any image that cannot be proven byte-identical after decoding, keep original PNG.
"""
import copy,hashlib,io,json,struct,sys,os
from pathlib import Path
from PIL import Image

SOURCE_EXPECTED='eef69d28dd8d53b5934442279a8b027bdfbfa157'
EXT='EXT_texture_webp'
def pad4(b,pad=b'\0'):
 return b+pad*((-len(b))%4)
def readglb(path):
 b=path.read_bytes()
 assert b[:4]==b'glTF' and struct.unpack_from('<II',b,4)==(2,len(b))
 off=12;jsondoc=None;binary=None
 while off<len(b):
  size,kind=struct.unpack_from('<I4s',b,off);off+=8
  chunk=b[off:off+size];off+=size
  if kind==b'JSON':jsondoc=json.loads(chunk)
  if kind==b'BIN\0':binary=chunk
 assert jsondoc is not None and binary is not None
 return b,jsondoc,binary
def gitblob(b):
 return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def pack(js,binary):
 jsbytes=pad4(json.dumps(js,separators=(',',':'),ensure_ascii=False).encode(),b' ')
 binbytes=pad4(binary)
 total=12+8+len(jsbytes)+8+len(binbytes)
 return b'glTF'+struct.pack('<II',2,total)+struct.pack('<I4s',len(jsbytes),b'JSON')+jsbytes+struct.pack('<I4s',len(binbytes),b'BIN\0')+binbytes
def build(master,out):
 original,js,buf=readglb(master)
 assert gitblob(original)==SOURCE_EXPECTED,'Original GLB changed; refusing to optimize different file'
 images=js.get('images',[]);textures=js.get('textures',[])
 assert len(images)==15 and len(textures)==15
 bv=js['bufferViews']
 rewrites={}
 image_records=[]
 for image_index,img in enumerate(images):
  view_index=img.get('bufferView')
  assert view_index is not None,'Source images must be embedded'
  view=bv[view_index]
  data=buf[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
  mime=img.get('mimeType')
  record=dict(index=image_index,name=img.get('name'),original_mime=mime,source_bytes=len(data),
    result_mime=mime,result_bytes=len(data),exact_pixels=True,used_webp=False)
  if mime=='image/png':
   source=Image.open(io.BytesIO(data));source.load()
   # A source with 16-bit channels needs unmodified original bytes,
   # never quantize and pretend it is pixel-identical.
   if source.mode not in ('RGB','RGBA','L','LA'):
    record['reason']='source format '+source.mode+' preserved'
   else:
    destbuf=io.BytesIO()
    source.save(destbuf,format='WEBP',lossless=True,method=6,exact=True)
    webp=destbuf.getvalue()
    candidate=Image.open(io.BytesIO(webp));candidate.load()
    exact=(source.size==candidate.size and source.convert('RGBA').tobytes()==candidate.convert('RGBA').tobytes())
    record['original_mode']=source.mode
    record['webp_mode']=candidate.mode
    if exact and len(webp)<len(data):
     rewrites[view_index]=webp
     img['mimeType']='image/webp'
     record.update(result_mime='image/webp',result_bytes=len(webp),used_webp=True)
    else:
     record['reason']='not byte-identical decoded or not smaller'
     record['exact_pixels']=exact
  image_records.append(record)
 # For each texture using WebP, Khronos requires extension.source instead
 # of core source; it remains universally browser-decodable without rescaling.
 changed_images={r['index'] for r in image_records if r['used_webp']}
 if changed_images:
  for tex in textures:
   if tex.get('source') in changed_images:
    old=tex.pop('source')
    tex.setdefault('extensions',{})[EXT]={'source':old}
  js.setdefault('extensionsUsed',[])
  if EXT not in js['extensionsUsed']:js['extensionsUsed'].append(EXT)
  js.setdefault('extensionsRequired',[])
  if EXT not in js['extensionsRequired']:js['extensionsRequired'].append(EXT)
 # Repacks bufferViews but does not modify a single byte of geometry/accessors.
 # Byte offsets are updated in their original order and padded to four bytes.
 outputbin=bytearray()
 nonimage_original=[]
 for index,view in enumerate(bv):
  old_data=buf[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
  new_data=rewrites.get(index,old_data)
  while len(outputbin)%4:outputbin.append(0)
  view['byteOffset']=len(outputbin)
  view['byteLength']=len(new_data)
  outputbin.extend(new_data)
  if index not in rewrites:
   nonimage_original.append((index,hashlib.sha256(old_data).hexdigest()))
 js['buffers'][0]['byteLength']=len(outputbin)
 new=pack(js,bytes(outputbin));cand=out/'door-herrero-v082-b-lossless-webp-candidate.glb'
 cand.write_bytes(new)
 nb,njs,nbytes=readglb(cand)
 # Every non-image bufferView must retain exact bytes, including vertex and index data.
 for index,digest in nonimage_original:
  view=njs['bufferViews'][index]
  payload=nbytes[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
  assert hashlib.sha256(payload).hexdigest()==digest,f'Non-image bufferView {index} changed!'
 # Every embedded image must have IDENTICAL decoded pixels, or unchanged source bytes.
 nims=njs['images']
 for idx,img in enumerate(nims):
  v=njs['bufferViews'][img['bufferView']]
  image=nbytes[v['byteOffset']:v['byteOffset']+v['byteLength']]
  _,og,ob=readglb(master)
  ov=og['bufferViews'][og['images'][idx]['bufferView']]
  raw=ob[ov.get('byteOffset',0):ov.get('byteOffset',0)+ov['byteLength']]
  if img.get('mimeType')=='image/webp':
   a=Image.open(io.BytesIO(raw));b=Image.open(io.BytesIO(image));a.load();b.load()
   assert a.size==b.size and a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes(),f'Pixel mismatch: {idx}'
  else:assert raw==image,'The fallback source changed bytes'
 expected_triangles=25720
 def tris(doc):
  total=0
  for mesh in doc.get('meshes',[]):
   for pr in mesh.get('primitives',[]):
    total+=doc['accessors'][pr['indices']]['count']//3
  return total
 assert tris(njs)==expected_triangles
 _,origdoc,_=readglb(master)
 # Geometry, node hierarchy, PBR values, animation data stay strictly identical:
 for key in ('nodes','meshes','accessors','materials','samplers','scenes','scene','animations','skins','cameras'):
  assert njs.get(key)==origdoc.get(key),f'Unapproved change in {key}'
 target=sum(x['result_bytes'] for x in image_records)
 orig=sum(x['source_bytes'] for x in image_records)
 report=dict(
  approved_original='DO NOT TOUCH',source_sha256=hashlib.sha256(original).hexdigest(),
  candidate_sha256=hashlib.sha256(new).hexdigest(),
  original_bytes=len(original),candidate_bytes=len(new),
  reduction_pct=round(100*(1-len(new)/len(original)),2),
  original_texture_bytes=orig,candidate_texture_bytes=target,
  original_triangles=expected_triangles,candidate_triangles=expected_triangles,
  vertex_index_buffers_byte_identical=True,original_material_pbr_unchanged=True,
  texture_pixel_differences=0,pixel_loss_pct=0.0,
  quality_constraint_pct=2.5,quality_target_pct=1.5,
  images_reencoded=sum(bool(x['used_webp']) for x in image_records),
  images_preserved=len(image_records)-sum(bool(x['used_webp']) for x in image_records),
  extension_required=EXT in njs.get('extensionsRequired',[]),
  runtime_playcanvas_test='PENDING_BROWSER_VERIFICATION',
  blender_cycles_hdr_comparison='PENDING',
  user_visual_approval='PENDING',
  images=image_records)
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 (out/'README.txt').write_text('CANDIDATE ONLY; V082-B original approved GLB untouched.\\n'+
  'Lossless WebP decode matches source pixels 100%; geometry, material and all indices unchanged.\\n'+
  'Use only after runtime PlayCanvas browser test, Blender 4.5.13 HDRI render comparisons, and user visual approval.\\n')
 print('LOSSLESS V082B RESULT',json.dumps({k:v for k,v in report.items() if k!='images'},ensure_ascii=False))
 for item in image_records:print('OPTIMIZED IMAGE',json.dumps(item,ensure_ascii=False))
if __name__=='__main__':
 source=Path(sys.argv[1])
 dest=Path(sys.argv[2])
 dest.mkdir(parents=True,exist_ok=True)
 build(source,dest)
