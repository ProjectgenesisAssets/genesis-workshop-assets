#!/usr/bin/env python3
"""Fix original V038 GLB malformed BIN chunk identifier without altering geometry.

Confirmed by PlayCanvas GLB parse: expected 0x004E4942 ('BIN\\0'),
received 0x5c4e4942 ('BIN\\\\'). Do not change masks, emissive or vertices.
"""
import struct, sys, json
from pathlib import Path
source=Path(sys.argv[1]);target=Path(sys.argv[2])
glb=bytearray(source.read_bytes())
assert glb[:4]==b'glTF' and struct.unpack_from('<I',glb,4)[0]==2
assert struct.unpack_from('<I',glb,8)[0]==len(glb)
json_len,tag=struct.unpack_from('<I4s',glb,12)
assert tag==b'JSON'
document=json.loads(glb[20:20+json_len])
at=20+json_len
length,chunk_tag=struct.unpack_from('<I4s',glb,at)
assert chunk_tag in (b'BIN\\',b'BIN\\0',b'BIN\\x00',b'BIN\\\x00',b'BIN\x00'),repr(chunk_tag)
assert at+8+length==len(glb),(len(glb),at,length)
glb[at+4:at+8]=b'BIN\x00'
assert struct.unpack_from('<I4s',glb,at)[1]==b'BIN\x00'
assert document.get('meshes') and document.get('nodes')
target.parent.mkdir(parents=True,exist_ok=True)
target.write_bytes(glb)
print(json.dumps({'original_tag':str(chunk_tag),'fixed':'BIN\\0','bytes':len(glb),'mesh_count':len(document['meshes']),'material_count':len(document.get('materials',[])),'status':'EXPERIMENTAL_BINARY_HEADER_REPAIR'}))
