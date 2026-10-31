#!/usr/bin/env python3
"""Independent technical QA and contact sheet. DO NOT call this visual approval.
Require true CC0 PBR channels, multi-view imagery, GLB integrity, a Blender master.
"""
from pathlib import Path
import sys,json,hashlib,struct
from PIL import Image,ImageStat,ImageDraw
slug=sys.argv[1]
base=Path(f'production/tutorial_materials/generated/{slug}')
config=json.loads(Path(f'production/tutorial_materials/config/{slug}.json').read_text())
model=base/f'{slug}_{config["version"].lower()}_candidate.glb'
master=base/f'{slug}_{config["version"].lower()}_master.blend'
provenance=json.loads((base/'source/provenance.json').read_text())
assert model.stat().st_size>20000 and model.stat().st_size<30000000, ('BAD_GLb_SIZE',model.stat().st_size)
assert master.stat().st_size>100000, 'Missing Blender editable master'
with model.open('rb') as f:
    magic,ver,length=struct.unpack('<4sII',f.read(12))
    assert magic==b'glTF' and ver==2 and length==model.stat().st_size
    jsize,jtype=struct.unpack('<II',f.read(8));assert jtype==0x4e4f534a
    gltf=json.loads(f.read(jsize))
assert len(gltf.get('meshes',[]))>=1
assert len(gltf.get('materials',[]))>=1
assert len(gltf.get('images',[]))>=3, 'Missing photographed PBR image maps'
triangles=0
for mesh in gltf['meshes']:
    for p in mesh.get('primitives',[]):
        if p.get('mode',4)==4:
            accessor=p.get('indices')
            triangles+=(gltf['accessors'][accessor]['count'] if accessor is not None else gltf['accessors'][p['attributes']['POSITION']]['count'])//3
assert 2000<=triangles<=180000,('Unreasonable geo complexity',triangles)
for mat in gltf['materials']:
    assert mat.get('pbrMetallicRoughness',{}).get('baseColorTexture'), ('Untextured base color',mat.get('name'))
    assert mat.get('normalTexture'),('Missing scanned normal',mat.get('name'))
    assert mat.get('pbrMetallicRoughness',{}).get('roughnessFactor',1)>0.0
views=('hero','side','top','back','macro')
images=[]
for v in views:
    file=base/(v+'.png')
    assert file.stat().st_size>30000,('Missing render',v)
    with Image.open(file) as im:
        assert im.width>=800 and im.height>=800
        rgba=im.convert('RGBA')
        alo,ahi=rgba.getchannel('A').getextrema()
        assert alo==0 and ahi==255,('No transparency',v)
        bbox=rgba.getchannel('A').getbbox()
        assert bbox and (bbox[2]-bbox[0])>65 and (bbox[3]-bbox[1])>65
        # Bright pink in Blender indicates missing PBR image paths, not valid art.
        sample=rgba.resize((160,160),Image.Resampling.NEAREST)
        subject=[p for p in sample.getdata() if p[3]>100]
        magenta=sum(1 for p in subject if p[0]>235 and p[2]>160 and p[1]<215)
        assert subject and magenta/len(subject)<.30,('BLENDER_MISSING_TEXTURES_PINK',v,magenta/len(subject))
        images.append(rgba.convert('RGB'))
poster=Image.open(base/'inventory_poster_rgba.png').convert('RGBA')
assert poster.size==(640,640)
assert poster.getchannel('A').getextrema()==(0,255)
assert len(provenance['photographic_scans'])==len(config['scans'])*3
assert all(x['license']=='CC0' for x in provenance['photographic_scans'])
# Three-angle contact sheet and closer views are for HUMAN review, not ML aesthetic scores.
width=2580;height=1840
board=Image.new('RGB',(width,height),(27,29,34))
draw=ImageDraw.Draw(board)
draw.text((26,17),f'PROJECT GENESIS / {config["name"].upper()} / V001 / SIX REAL BLENDER VIEWS',fill=(232,216,189),stroke_width=0)
labels=['HERO 3/4','SIDE','TOP','BACK','MACRO']
for i,(pic,label) in enumerate(zip(images,labels)):
    col=i%3;row=i//3
    im=pic.resize((790,790),Image.Resampling.LANCZOS)
    x=35+col*850;y=75+row*850
    board.paste(im,(x,y))
    draw.text((x+5,y+795),label,fill=(236,221,199))
draw.text((1750,1720),'PHOTOGRAPHIC CC0 SURFACES | PROCEDURAL GEOMETRY',fill=(202,184,155))
draw.text((1750,1750),'PBR / NOT ARTISTICALLY APPROVED',fill=(210,165,119))
board.save(base/'multi_view_contact_sheet.jpg',quality=92,optimize=True)
report={
 'asset':slug,'name':config['name'],'version':config['version'],'status':'candidate_needs_human_visual_approval',
 'geometry_technique':'hand-directed parametric Blender geometry, not full object photoscan',
 'photo_texture_license':'CC0 Poly Haven','sources':[x['page'] for x in provenance['photographic_scans'][::3]],
 'source_provenance':'source/provenance.json',
 'model':str(model),'bytes':model.stat().st_size,'sha256':hashlib.sha256(model.read_bytes()).hexdigest(),
 'triangles':triangles,'mesh_count':len(gltf['meshes']),'materials':len(gltf['materials']),
 'images_embedded':len(gltf['images']),'master':str(master),'poster':str(base/'inventory_poster_rgba.png'),
 'views':list(views),'reference_notes':config['art_direction'],
 'technical_checks':{'glb_header':True,'normal_maps_embedded':True,'scanned_albedo':True,'multi_views':True,
 'transparent_poster':True,'blender_editable_master':True,'license_verified':True},
 'visual_score':None,'approved_for_game':False}
(base/(config['version']+'_AUDIT.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('PASS_CANDIDATE_QA',json.dumps({'slug':slug,'triangles':triangles,'mb':round(model.stat().st_size/1e6,2),'views':len(views)}))
