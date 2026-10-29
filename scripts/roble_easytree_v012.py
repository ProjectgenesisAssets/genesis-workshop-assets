# V012: independent free Easy-Tree geometry-nodes oak probe.
# Generated source geometry only. No game approval until real visual audit.
import bpy,sys,json,random,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,'/tmp')
import easy_tree_plugin
easy_tree_plugin.register()
random.seed(12121)
out=Path('output_plaza_easytree_v012/oak');out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.tree_preset='LARGE'
bpy.context.scene.season='SUMMER'
result=bpy.ops.object.add_tree_tool()
assert 'FINISHED' in result,('EASYTREE_OPERATOR_FAILED',str(result))
obj=bpy.context.active_object
assert obj and obj.type=='MESH',('NO_EASYTREE',str(obj))
obj.name='Oak_EasyTree_V012_Proof'
mod=next((m for m in obj.modifiers if m.type=='NODES'),None)
assert mod and mod.node_group,'NO_NODE_GENERATOR'
# Keep branching moderated before realizing geometry to avoid waste.
mod['Socket_27']=3
mod['Socket_28']=5.5
mod['Socket_32']=2.0
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
audit={'species':'oak','version':'V012','generator':'Easy-Tree GPL-3.0 geometry nodes',
       'triangles_raw':raw_tri,'triangle_limit':60000,'within_budget':raw_tri<=60000,
       'dimensions_m':list(dimensions),'materials':matnames,'approved':False,
       'status':'Visual/source probe only; no decimation and no game export before quality check'}
(out/'AUDIT.json').write_text(json.dumps(audit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((out/'oak_easytree_v012.blend').resolve()))
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
print('V012_EASYTREE_PROBE_AUDIT',json.dumps(audit))
