# Project Genesis charcoal V009. Real mesh renders, no substitute silhouettes.
import bpy, json, math
from pathlib import Path
from mathutils import Vector
OUT=Path('output_charcoal_pile_v009').resolve()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(OUT/'PG_Charcoal_Pile_V009_WEB.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
if len(meshes)<4: raise RuntimeError('V009 model did not import four pieces')
# Imported glTF has an epsilon-scale source node; exclude it from framing.
visible=[o for o in meshes if 'master_source_hidden' not in o.name]
if len(visible)!=4: print('INFO mesh names',[o.name for o in meshes])
pts=[]
for ob in visible:
    pts.extend([ob.matrix_world@Vector(p) for p in ob.bound_box])
center=Vector([(min(p[i] for p in pts)+max(p[i] for p in pts))/2 for i in range(3)])
ext=max(max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3))
world=bpy.data.worlds.new('Neutral inspection studio')
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.34,.35,.37,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.54
def add_area(name,pos,power,diam):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=diam
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
    o.location=pos;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
add_area('Large softbox',center+Vector((3.2,-3.5,4.4)),1050,4.5)
add_area('Fibre grazing light',center+Vector((-4,1.0,2.8)),850,3)
add_area('Ambient fill',center+Vector((0,4.0,1.0)),340,4.0)
camdata=bpy.data.cameras.new('V009 review cam');camdata.type='ORTHO'
cam=bpy.data.objects.new('V009 review cam',camdata);bpy.context.collection.objects.link(cam)
bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1000;scene.render.resolution_y=780
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.5
for label,offset,scale in [
 ('three_quarter',(3.8,-5,3.0),2.9),
 ('side',(5.0,-1.5,2.25),2.65),
 ('overhead',(1.5,-2.9,5.6),2.75),
 ('alternate',(-3.2,-4.0,2.8),2.83)
]:
    cam.location=center+Vector(offset)
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    camdata.ortho_scale=max(2.0,ext*1.05)*scale/2.4
    scene.render.filepath=str(OUT/(label+'.png'))
    bpy.ops.render.render(write_still=True)
print('CHARCOAL_PILE_V009_RENDERS_COMPLETED')
