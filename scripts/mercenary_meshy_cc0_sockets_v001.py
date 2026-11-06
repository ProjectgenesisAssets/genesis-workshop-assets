"""Experimental Project Genesis rig/socket validation; not game integration.
Meshy 7.1 character CC0 according to https://vibeassets.io/a/9h7odik5fl
Blender 4.5.13 LTS / GitHub Actions / Cycles / Poly Haven 32-bit HDRI.
"""
import bpy, os, json, math, struct, hashlib
from mathutils import Vector
from pathlib import Path

out=Path("output/mercenary_meshy_cc0_v001");out.mkdir(parents=True,exist_ok=True)
src=Path("sources/mercenary_captain_meshy_cc0.glb")
hdr=Path("sources/studio_small_09_2k.hdr")
sword=Path("sources/mercenary_sword_test_only.glb")
shield=Path("sources/mercenary_shield_test_only.glb")

def read_glb(p):
    data=p.read_bytes()
    assert data[:4]==b'glTF' and struct.unpack_from('<I',data,4)[0]==2
    assert struct.unpack_from('<I',data,8)[0]==len(data)
    size,chunk=struct.unpack_from('<I4s',data,12)
    assert chunk==b'JSON'
    return json.loads(data[20:20+size].decode('utf-8'))

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1048576),b''):h.update(c)
    return h.hexdigest()

def hand_bone(arm,side):
    terms=('righthand','handright','handr','rightwrist','rwrist') if side=='right' else ('lefthand','handleft','handl','leftwrist','lwrist')
    scored=[]
    for b in arm.data.bones:
        n=b.name.lower().replace('_','').replace('-','').replace('.','').replace(':','')
        for t in terms:
            if n.endswith(t):scored.append((len(t),b.name))
    if not scored:raise RuntimeError('Hand bone '+side+' missing. Bones: '+str([b.name for b in arm.data.bones]))
    return sorted(scored,reverse=True)[0][1]

def socket(arm,bone,name):
    e=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(e)
    e.empty_display_type='ARROWS';e.empty_display_size=.07
    e.parent=arm;e.parent_type='BONE';e.parent_bone=bone
    e.location=(0,0,0);e.rotation_euler=(0,0,0)
    e['genesis_socket']=True;e['bone_name']=bone
    return e

def add_temp_gear(path,parent,name,rotation):
    previous=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    new=set(bpy.context.scene.objects)-previous
    assert any(o.type=='MESH' for o in new),'No mesh for temporary '+name
    origin=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(origin)
    origin.empty_display_type='CUBE';origin.empty_display_size=.04
    for o in new:
        if o.parent is None:
            m=o.matrix_world.copy();o.parent=origin;o.matrix_world=m
    origin.parent=parent;origin.location=(0,0,0)
    origin.rotation_euler=tuple(math.radians(v) for v in rotation)
    origin['test_only']='NOT APPROVED: original game vendor mesh for mounting diagnosis'
    return origin

def check_export(p):
    j=read_glb(p)
    nodes=[x.get('name','') for x in j.get('nodes',[])]
    assert j.get('skins'),'The exported GLB lost its skin'
    assert j.get('animations'),'The exported GLB lost its animations'
    assert 'GENESIS_SOCKET_RIGHT_HAND' in nodes and 'GENESIS_SOCKET_LEFT_HAND' in nodes,'Lost socket nodes '+str(nodes)
    return {'bytes':p.stat().st_size,'sha256':digest(p),'skin_count':len(j['skins']),
            'animation_count':len(j['animations']),
            'animation_names':[x.get('name') for x in j['animations']],
            'socket_nodes':[n for n in nodes if n.startswith('GENESIS_SOCKET_')]}

def save_glb(name):
    p=out/name
    bpy.ops.export_scene.gltf(filepath=str(p.resolve()),export_format='GLB',
        export_animations=True,export_nla_strips=True,export_yup=True,export_extras=True)
    return check_export(p)

def bounds(objects):
    pts=[o.matrix_world@Vector(p) for o in objects if o.type=='MESH' for p in o.bound_box]
    assert pts,'Missing character geometry'
    low=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return low,high

def render(geometry):
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
    scene.render.resolution_x=640;scene.render.resolution_y=640
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    world=bpy.data.worlds.new('PolyHaven_StudioSmall09_32bit_HDRI');scene.world=world;world.use_nodes=True
    nt=world.node_tree;nt.nodes.clear()
    env=nt.nodes.new('ShaderNodeTexEnvironment')
    env.image=bpy.data.images.load(str(hdr.resolve()))
    assert env.image.file_format in ('HDR','OPEN_EXR'),'HDRI cannot be SDR'
    bg=nt.nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.72
    dest=nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(env.outputs['Color'],bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'],dest.inputs['Surface'])
    cd=bpy.data.cameras.new('Genesis_QA_Camera')
    cam=bpy.data.objects.new('Genesis_QA_Camera',cd)
    scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
    mn,mx=bounds(geometry);center=(mn+mx)*.5
    r=max((mx-mn).x,(mx-mn).y,(mx-mn).z,1.2);cd.ortho_scale=r*1.55
    for label,vec in [('front',(0,-1,.18)),('three_quarter',(.75,-1,.26)),('side',(1,0,.20)),('back',(0,1,.18))]:
        cam.location=center+Vector(vec).normalized()*r*2.6
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        p=out/(label+'.png');scene.render.filepath=str(p.resolve())
        bpy.ops.render.render(write_still=True)
        assert p.stat().st_size>10000,'Missing preview '+label

original=read_glb(src)
assert len(original.get('skins',[]))>=1,'Source not skinned'
assert len(original.get('animations',[]))>=1,'Source not animated'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src.resolve()))
arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
assert arms,'No armature in source'
arm=max(arms,key=lambda x:len(x.data.bones))
rb=hand_bone(arm,'right');lb=hand_bone(arm,'left')
character=[o for o in bpy.context.scene.objects if o.type=='MESH']
right=socket(arm,rb,'GENESIS_SOCKET_RIGHT_HAND')
left=socket(arm,lb,'GENESIS_SOCKET_LEFT_HAND')
bpy.context.view_layer.update()
clean=save_glb('mercenary_sockets_clean_UNAPPROVED.glb')
add_temp_gear(sword,right,'TEST_ONLY_SWORD',rotation=(90,0,90))
add_temp_gear(shield,left,'TEST_ONLY_SHIELD',rotation=(90,0,-10))
bpy.context.view_layer.update()
demo=save_glb('mercenary_with_TEMPorary_gear_UNAPPROVED.glb')
render(character)
report={'status':'EXPERIMENT_ONLY_UNAPPROVED','source':'https://vibeassets.io/a/9h7odik5fl',
    'license':'CC0 claimed by source publisher','source_hash':digest(src),
    'source_bytes':src.stat().st_size,'source_animation_names':[a.get('name') for a in original['animations']],
    'source_skin_count':len(original['skins']),'armature_bones':len(arm.data.bones),
    'right_hand_bone':rb,'left_hand_bone':lb,'clean':clean,'test_equipment':demo,
    'test_equipment_source':'gburdesedev/Project-genesis / vendor mercSword10 and mercShield10 only',
    'real_approved_equipment_integrated':False,'game_tested':False,'visual_approved':False,
    'hdri':'Poly Haven Studio Small 09 2K 32-bit Radiance HDR','renderer':'Cycles',
    'render_views':['front.png','three_quarter.png','side.png','back.png'],
    'warning':'Hand offsets and animation clipping must be visually reviewed before integration.'}
(out/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('GENESIS_MERCENARY_QA',json.dumps(report,ensure_ascii=False))
