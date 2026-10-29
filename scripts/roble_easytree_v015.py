# V015: sculpted organic oak test: three-branch branching, finer photographic leaves.
# Generated source geometry only. No game approval until real visual audit.
import bpy,sys,json,random,math
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,'/tmp')
import easy_tree_plugin
easy_tree_plugin.register()
random.seed(12121)
out=Path('output_plaza_easytree_v015/oak');out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.tree_preset='LARGE'
bpy.context.scene.season='SUMMER'
result=bpy.ops.object.add_tree_tool()
assert 'FINISHED' in result,('EASYTREE_OPERATOR_FAILED',str(result))
obj=bpy.context.active_object
assert obj and obj.type=='MESH',('NO_EASYTREE',str(obj))
obj.name='Oak_EasyTree_V015_Proof'
mod=next((m for m in obj.modifiers if m.type=='NODES'),None)
assert mod and mod.node_group,'NO_NODE_GENERATOR'
# Natural oak architecture: shorter bare trunk, wider asymmetric primary boughs.
mod['Socket_27']=4
mod['Socket_40']=1
mod['Socket_25']=1  # three primary branches per level, instead of two
mod['Socket_28']=7
mod['Socket_29']=0.57
mod['Socket_30']=0.28
mod['Socket_31']=0.78
mod['Socket_32']=2.8
# This generator's default minimum leaf height is 15 m: our oak is ~7 m.
mod['Socket_12']=2
mod['Socket_13']=7.0
mod['Socket_19']=True
mod['Socket_39']=True
obj.update_tag()
bpy.context.view_layer.update()
print('EASYTREE_NODE_GROUP',mod.node_group.name)
for item in mod.node_group.interface.items_tree:
    if getattr(item,'item_type','')=='SOCKET' and getattr(item,'in_out','')=='INPUT':
        print('EASYTREE_SOCKET',item.name,item.identifier,str(getattr(item,'default_value',''))[:80])
bpy.ops.object.convert(target='MESH')
obj=bpy.context.object
assert obj.type=='MESH'
raw_tri=sum(len(p.vertices)-2 for p in obj.data.polygons)
assert raw_tri>1000,('EMPTY_EASYTREE_GENERATOR',raw_tri)
matnames=[m.name for m in obj.data.materials]
bounds=[obj.matrix_world @ Vector(c) for c in obj.bound_box]
minimum=Vector(tuple(min(v[i] for v in bounds) for i in range(3)))
maximum=Vector(tuple(max(v[i] for v in bounds) for i in range(3)))
center=(minimum+maximum)*.5
dimensions=maximum-minimum
print('EASYTREE_PROBE_DIMENSIONS',list(dimensions),'MATERIALS',matnames,'TRIANGLES',raw_tri)
# Choose spatially separated branch tips and upper twig surfaces; avoid low trunk.
# Scatter photo leaves along multiple actual branch tips; leave voids between foliated branches.
wood_vertices=[v.co.copy() for v in obj.data.vertices]
eligible=[p for p in wood_vertices
          if p.z>minimum.z+dimensions.z*.40
          and (math.hypot(p.x-center.x,p.y-center.y)>.85
               or p.z>minimum.z+dimensions.z*.80)]
eligible.sort(key=lambda p:(p.z-minimum.z)*.12+
              math.hypot(p.x-center.x,p.y-center.y)*1.15+random.random()*.8,reverse=True)
anchors=[]
for point in eligible:
    if all((point-other).length>.48 for other in anchors):
        anchors.append(point)
    if len(anchors)>=155:break
print('V015_BRANCH_TIP_ANCHORS',len(anchors))
# Photo-scanned six oak leaves from ambientCG LeafSet016, CC0 1.0.
# Pack source color and black/white opacity into one portable GLB RGBA atlas.
# Attribution: https://ambientcg.com/view?id=LeafSet016 (CC0, optional credit).
src_dir=Path('/tmp/genesis-leafset016')
color_path=src_dir/'LeafSet016_1K-JPG_Color.jpg'
opacity_path=src_dir/'LeafSet016_1K-JPG_Opacity.jpg'
assert color_path.is_file() and opacity_path.is_file(), 'MISSING_CC0_PHOTO_LEAF_ATLAS'
color_source=bpy.data.images.load(str(color_path),check_existing=False)
opacity_source=bpy.data.images.load(str(opacity_path),check_existing=False)
N=color_source.size[0]
assert color_source.size[:]==opacity_source.size[:], 'PHOTO_ALPHA_SIZE_MISMATCH'
rgba_flat=np.empty(N*N*4,dtype=np.float32)
mask_flat=np.empty(N*N*4,dtype=np.float32)
color_source.pixels.foreach_get(rgba_flat)
opacity_source.pixels.foreach_get(mask_flat)
rgba=rgba_flat.reshape(N,N,4)
mask=mask_flat.reshape(N,N,4)
rgba[:,:,:3]*=np.array((.74,.80,.69),dtype=np.float32)
rgba[:,:,3]=(mask[:,:,0]>.73).astype(np.float32)
image=bpy.data.images.new('Oak V015 ambientCG LeafSet016 CC0 photos',width=N,height=N,alpha=True)
image.pixels.foreach_set(rgba.reshape(-1))
image.filepath_raw=str((out/'oak_leaf_atlas.png').resolve())
image.file_format='PNG'
image.save()
image.pack()
foliage=bpy.data.materials.new('Oak V015 cutout leaves');foliage.use_nodes=True
bs=foliage.node_tree.nodes.get('Principled BSDF')
tex=foliage.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
foliage.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
quant=foliage.node_tree.nodes.new('ShaderNodeMath');quant.operation='ROUND'
foliage.node_tree.links.new(tex.outputs['Alpha'],quant.inputs[0]);foliage.node_tree.links.new(quant.outputs[0],bs.inputs['Alpha'])
foliage.use_backface_culling=False
v=[];f=[];uvdata=[]
assert anchors,('NO_TIP_ANCHORS',len(obj.data.vertices))
for i in range(17000):
    pos=random.choice(anchors)+Vector((random.gauss(0,.31),random.gauss(0,.31),random.gauss(0,.23)))
    size=random.uniform(.062,.104)
    normal=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-.3,1))).normalized()
    side=normal.cross(Vector((0,0,1)))
    if side.length<.05:side=Vector((1,0,0))
    side.normalize();up=normal.cross(side).normalized()
    theta=random.random()*math.tau
    x=(side*math.cos(theta)+up*math.sin(theta))*size
    y=(-side*math.sin(theta)+up*math.cos(theta))*size
    start=len(v)
    for point in (pos-x-y,pos+x-y,pos+x+y,pos-x+y):v.append(tuple(point))
    f.extend([(start,start+1,start+2),(start,start+2,start+3)])
    tile=random.randrange(6);u0=(tile%3)/3;v0=(tile//3)*.5
    quad=[(u0,v0),(u0+1/3,v0),(u0+1/3,v0+.5),(u0,v0+.5)]
    uvdata.extend([(quad[0],quad[1],quad[2]),(quad[0],quad[2],quad[3])])
mesh=bpy.data.meshes.new('Oak botanical foliage');mesh.from_pydata(v,[],f);mesh.update()
mesh.materials.append(foliage);layer=mesh.uv_layers.new(name='UVMap')
for poly,coords in zip(mesh.polygons,uvdata):
    for li,uv in zip(poly.loop_indices,coords):layer.data[li].uv=uv
leaves=bpy.data.objects.new('Oak foliage cards',mesh);bpy.context.collection.objects.link(leaves)
audit={'species':'oak','version':'V015','generator':'Easy-Tree GPL-3.0 geometry nodes',
       'triangles_raw':raw_tri,'triangles':raw_tri+len(mesh.polygons),'triangle_limit':60000,'within_budget':raw_tri+len(mesh.polygons)<=60000,
       'dimensions_m':list(dimensions),'materials':matnames+[foliage.name],'leaf_atlas':'ambientCG LeafSet016 CC0 photos','approved':False,
       'status':'Asymmetric 3-branch oak + fine CC0 photographed leaves; GLB technical validation and visual review pending'}
assert audit['within_budget'],('V015_TRIANGLES_OVER_BUDGET',audit['triangles'])
(out/'AUDIT.json').write_text(json.dumps(audit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((out/'oak_easytree_v015.blend').resolve()))
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True);leaves.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str((out/'oak_easytree_v015.glb').resolve()),
                          export_format='GLB',use_selection=True,export_apply=True)

# This probe intentionally renders the raw, un-decimated generated mesh.
ground_mat=bpy.data.materials.new('NeutralStage');ground_mat.diffuse_color=(.40,.41,.39,1)
bpy.ops.mesh.primitive_plane_add(size=max(50,dimensions.x*3,dimensions.y*3),
                                 location=(center.x,center.y,minimum.z-.10))
bpy.context.object.data.materials.append(ground_mat)
span=max(dimensions.x,dimensions.y,dimensions.z,3)
for pwr,loc in [(1800,center+Vector((span,-span*.7,span*1.6))),
                (1100,center+Vector((-span,span,span*1.2)))]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    lamp=bpy.context.object;lamp.data.energy=pwr;lamp.data.shape='DISK';lamp.data.size=max(3,span*.6)
bpy.ops.object.camera_add()
cam=bpy.context.object
scene=bpy.context.scene;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16
scene.cycles.use_denoising=True
scene.view_settings.view_transform='AgX'
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
for name,direction in [('front',Vector((0,-1,.28))),('three_quarter',Vector((.65,-1,.40)))]:
    cam.location=center+direction.normalized()*span*2.9
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=span*1.65
    scene.render.filepath=str((out/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
print('V015_EASYTREE_PROBE_AUDIT',json.dumps(audit))
