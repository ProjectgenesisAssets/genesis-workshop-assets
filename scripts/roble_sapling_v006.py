# Project Genesis Oak V006: official Sapling + fused voxel trunk prototype.
# Art QA first. Non-approved candidate, no paid assets.
import bpy,sys,json,math,random
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,'/tmp/blender-addons')
import add_curve_sapling
add_curve_sapling.register()
out=Path('output_plaza_v006/oak');out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
random.seed(7025)
# Parametric botanical branching from Blender's Sapling implementation.
bpy.ops.curve.tree_add(
    seed=7025,levels=3,scale=8.2,scaleV=.32,
    branches=(0,18,12,0),length=(1.0,.74,.60,.35),
    curveRes=(8,5,3,1),baseSize=.27,
    ratio=.028,ratioPower=1.15,
    shape='1',showLeaves=False,bevel=True,rootFlare=1.25,
    splitAngle=(0,27,24,0),
    rotate=(0,137.5,126,0),
    downAngle=(0,76,58,0),
)
curves=[o for o in bpy.context.scene.objects if o.type=='CURVE']
assert curves,'SAPLING_CURVE_NOT_CREATED'
# Take actual terminal branching locations from Sapling, before mesh conversion.
budpoints=[]
for tree_curve in curves:
    for spline in tree_curve.data.splines:
        points=[(tree_curve.matrix_world @ p.co) for p in spline.bezier_points] if spline.type=='BEZIER' else [(tree_curve.matrix_world @ Vector((p.co.x,p.co.y,p.co.z))) for p in spline.points]
        for pt in points[-3:]:
            if pt.z>3.15:budpoints.append(pt.copy())
print('SAPLING_FOLIAGE_ANCHORS',len(budpoints))
assert len(budpoints)>25
for o in bpy.context.selected_objects:o.select_set(False)
obj=max(curves,key=lambda o:len(o.data.splines))
obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.object.convert(target='MESH')
obj=bpy.context.object;obj.name='Oak_Sapling_Fused_Bark_V006'
pre=len(obj.data.polygons)
assert pre>500,('SAPLING_TOO_SIMPLE',pre)
# Voxel remesh performs spatial UNION at limb intersections.
obj.data.remesh_voxel_size=.075
obj.data.remesh_voxel_adaptivity=0.0
bpy.ops.object.voxel_remesh()
# Remove splinter components produced when tiny distal twigs are voxelized.
import bmesh
bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table()
remaining=set(bm.verts);groups=[]
while remaining:
    seed=remaining.pop();component=[seed];queue=[seed]
    while queue:
        v=queue.pop()
        for edge in v.link_edges:
            other=edge.other_vert(v)
            if other in remaining:
                remaining.remove(other);component.append(other);queue.append(other)
    groups.append(component)
groups.sort(key=len,reverse=True)
if len(groups)>1:
    drop=[v for component in groups[1:] for v in component]
    bmesh.ops.delete(bm,geom=drop,context='VERTS')
bm.to_mesh(obj.data);bm.free();obj.data.update()
print('FUSED_COMPONENTS',len(groups),'KEPT_VERTICES',len(groups[0]))
raw=sum(len(p.vertices)-2 for p in obj.data.polygons)
assert raw>1000,('VOXEL_REMESH_EMPTY',raw)
# Keep shape silhouette while capping runtime triangles.
if raw>35000:
    mod=obj.modifiers.new('Geometry budget decimate','DECIMATE')
    mod.ratio=min(1,35000/raw)
    bpy.ops.object.modifier_apply(modifier=mod.name)
for poly in obj.data.polygons:poly.use_smooth=True
# UVs rebuilt after remesh using smart projection.
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=.012)
bpy.ops.object.mode_set(mode='OBJECT')
bark=bpy.data.materials.new('Mature oak aged bark');bark.use_nodes=True
bs=bark.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.21,.145,.093,1)
bs.inputs['Roughness'].default_value=.92
obj.data.materials.clear();obj.data.materials.append(bark)
# Original alpha-cutout oak leaves, placed at branch ends; never remeshed into bark.
import numpy as np
rr=np.random.default_rng(1006)
N=512
atlas=np.zeros((N,N,4),np.float32)
for tile in range(4):
    row,col=divmod(tile,2)
    yy,xx=np.mgrid[0:256,0:256].astype(np.float32)
    t=(yy-26)/205
    u=(xx-128)/92
    lobe=(.72+.22*np.cos(t*math.pi*6+tile*.7))
    width=(np.sin(np.clip(t,0,1)*math.pi)**.75)*lobe
    mask=(t>=0)&(t<=1)&(np.abs(u)<=width)
    c=np.array((.28,.43,.105),dtype=np.float32)*(1+tile*.075)
    shade=np.clip(1.07+.20*np.sin(t*math.pi)+rr.normal(0,.07,(256,256)),.55,1.5)
    region=atlas[row*256:(row+1)*256,col*256:(col+1)*256]
    for j in range(3):region[:,:,j][mask]=np.clip(c[j]*shade,0,1)[mask]
    region[:,:,3][mask]=1
image=bpy.data.images.new('Oak V006 four botanical leaf silhouettes',width=N,height=N,alpha=True)
image.pixels.foreach_set(atlas.reshape(-1))
image.filepath_raw=str((out/'oak_leaf_atlas.png').resolve());image.file_format='PNG';image.save();image.pack()
foliage=bpy.data.materials.new('Oak V006 cutout leaves');foliage.use_nodes=True
bs=foliage.node_tree.nodes.get('Principled BSDF')
tex=foliage.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
foliage.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
quant=foliage.node_tree.nodes.new('ShaderNodeMath');quant.operation='ROUND'
foliage.node_tree.links.new(tex.outputs['Alpha'],quant.inputs[0]);foliage.node_tree.links.new(quant.outputs[0],bs.inputs['Alpha'])
foliage.use_backface_culling=False
v=[];f=[];uvdata=[]
assert budpoints
for i in range(2100):
    pos=random.choice(budpoints)+Vector((random.gauss(0,.34),random.gauss(0,.34),random.gauss(0,.26)))
    size=random.uniform(.17,.32)
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
    tile=random.randrange(4);u0=(tile%2)*.5;v0=(tile//2)*.5
    quad=[(u0,v0),(u0+.5,v0),(u0+.5,v0+.5),(u0,v0+.5)]
    uvdata.extend([(quad[0],quad[1],quad[2]),(quad[0],quad[2],quad[3])])
mesh=bpy.data.meshes.new('Oak botanical foliage');mesh.from_pydata(v,[],f);mesh.update()
mesh.materials.append(foliage);layer=mesh.uv_layers.new(name='UVMap')
for poly,coords in zip(mesh.polygons,uvdata):
    for li,uv in zip(poly.loop_indices,coords):layer.data[li].uv=uv
leaves=bpy.data.objects.new('Oak foliage cards',mesh);bpy.context.collection.objects.link(leaves)
tri=sum(len(p.vertices)-2 for p in obj.data.polygons)
tri+=len(mesh.polygons)
assert tri<60000,('TRIANGLE_CAP',tri)
audit={'species':'oak','version':'V006','technique':'Blender Sapling Tree Gen official addon + voxel union + shape-preserving decimate',
       'triangles':tri,'sapling_mesh_faces':pre,'pre_decimate_voxel_triangles':raw,
       'limit':60000,'approved':False,'review':'Sapling + fused branch topology + botanical leaf cards; visual approval pending'}
(out/'AUDIT.json').write_text(json.dumps(audit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((out/'oak_sapling_v006.blend').resolve()))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);leaves.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str((out/'oak_sapling_v006.glb').resolve()),
                          export_format='GLB',use_selection=True,export_apply=True)
# Render with neutral lighting to inspect joint topology, no foliage to hide artifacts.
bpy.ops.object.select_all(action='DESELECT')
ground_mat=bpy.data.materials.new('Ground');ground_mat.diffuse_color=(.35,.36,.34,1)
bpy.ops.mesh.primitive_plane_add(size=100)
bpy.context.object.data.materials.append(ground_mat)
for pwr,loc in [(1700,(8,-5,12)),(1200,(-5,4,9))]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    lamp=bpy.context.object;lamp.data.energy=pwr;lamp.data.shape='DISK';lamp.data.size=8
bpy.ops.object.camera_add()
cam=bpy.context.object
scene=bpy.context.scene;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=20
scene.cycles.use_denoising=True;scene.view_settings.view_transform='AgX'
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
for label,loc in [('front',(0,-12,7)),('three_quarter',(8,-11,7.5)),('side',(12,0,7))]:
    cam.location=loc;cam.rotation_euler=(Vector((0,0,4))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str((out/(label+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
leaves.hide_render=True
cam.location=(8,-11,7.5)
cam.rotation_euler=(Vector((0,0,4))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str((out/'skeleton_three_quarter.png').resolve())
bpy.ops.render.render(write_still=True)
print('V006_OAK_AUDIT',json.dumps(audit))
