#!/usr/bin/env python3
"""Lossless GLB container fix for Project Genesis V011 water animation.

Blender exported 62 independent animation clips. A <pc-anim> automatically
plays only the first clip; for a single 8s fountain cycle we must combine
channels/samplers while leaving ALL mesh, BIN, PBR and texture bytes untouched.
"""
from pathlib import Path
import json, struct, hashlib

root=Path('public/models')
source=root/'PG_Dolphin_Fountain_V011_PlayCanvas_Animated.glb'
target=root/'PG_Dolphin_Fountain_V011_PlayCanvas_Merged8s.glb'
report=root/'PG_Dolphin_Fountain_V011_PlayCanvas_Merged8s.json'

binary=source.read_bytes()
assert binary[:4]==b'glTF' and struct.unpack_from('<I',binary,4)[0]==2
assert struct.unpack_from('<I',binary,8)[0]==len(binary)
chunks=[]
pos=12
while pos<len(binary):
    size,typ=struct.unpack_from('<I4s',binary,pos)
    pos+=8
    chunks.append((typ,binary[pos:pos+size]))
    pos+=size
assert pos==len(binary)
assert chunks[0][0]==b'JSON'
obj=json.loads(chunks[0][1])
animations=obj.get('animations',[])
assert len(animations)>1,'Expected V011 multiple Blender clips'
combined={'name':'Escupitajo_8s','samplers':[],'channels':[]}
targets=set()
for anim in animations:
    offset=len(combined['samplers'])
    combined['samplers'].extend(anim['samplers'])
    for ch in anim['channels']:
        target=ch.get('target',{})
        identity=(target.get('node'),target.get('path'))
        assert identity not in targets, 'Duplicate animation target: '+repr(identity)
        targets.add(identity)
        newch=dict(ch)
        newch['sampler']=ch['sampler']+offset
        combined['channels'].append(newch)
assert len(combined['channels'])>=80,'Unexpected loss of animated fountain channels'
obj['animations']=[combined]
jsonraw=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8')
jsonraw+=b' '*((-len(jsonraw))%4)
outchunks=[(b'JSON',jsonraw),*chunks[1:]]
length=12+sum(8+len(blob) for typ,blob in outchunks)
out=bytearray(struct.pack('<4sII',b'glTF',2,length))
for typ,blob in outchunks:
    out.extend(struct.pack('<I4s',len(blob),typ))
    out.extend(blob)
assert len(out)==length and out[:4]==b'glTF'
assert outchunks[1:]==chunks[1:],'Any BIN modification is forbidden'
target.write_bytes(out)
info={
 'asset':'PG_Dolphin_Fountain_V011_PlayCanvas_Merged8s',
 'status':'GLB_ANIMATION_COMBINED_NOT_VISUALLY_APPROVED',
 'source_asset':source.name,
 'original_animation_clips':len(animations),
 'merged_animation_clips':1,
 'merged_animation_name':combined['name'],
 'channels':len(combined['channels']),
 'samplers':len(combined['samplers']),
 'unchanged_binary_chunks':len(chunks)-1,
 'render_bytes':len(out),
 'sha256':hashlib.sha256(out).hexdigest(),
 'duration_seconds':7.958,
 'note':'No mesh, material, geometry or texture changes; all original water tracks play in one 8s clip'
}
report.write_text(json.dumps(info,indent=2),encoding='utf8')
print(json.dumps(info))
