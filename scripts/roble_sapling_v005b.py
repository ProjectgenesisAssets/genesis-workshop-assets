# Project Genesis Oak V005B: official Sapling + fused voxel trunk prototype.
# Art QA first. Non-approved candidate, no paid assets.
import bpy,sys,json,math,random
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,'/tmp/blender-addons')
import add_curve_sapling
add_curve_sapling.register()
out=Path('output_plaza_v005b/oak');out.mkdir(parents=True,exist_ok=True)
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
for o in bpy.context.selected_objects:o.select_set(False)
obj=max(curves,key=lambda o:len(o.data.splines))
obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.object.convert(target='MESH')
obj=bpy.context.object;obj.name='Oak_Sapling_Fused_Bark_V005B'
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
tri=sum(len(p.vertices)-2 for p in obj.data.polygons)
assert tri<60000,('TRIANGLE_CAP',tri)
audit={'species':'oak','version':'V005B','technique':'Blender Sapling Tree Gen official addon + voxel union + shape-preserving decimate',
       'triangles':tri,'sapling_mesh_faces':pre,'pre_decimate_voxel_triangles':raw,
       'limit':60000,'approved':False,'review':'branch topology and silhouette; foliage is deliberately absent'}
(out/'AUDIT.json').write_text(json.dumps(audit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((out/'oak_sapling_v005b.blend').resolve()))
bpy.ops.export_scene.gltf(filepath=str((out/'oak_sapling_v005b.glb').resolve()),
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
print('V005B_OAK_AUDIT',json.dumps(audit))
