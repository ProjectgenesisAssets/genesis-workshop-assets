# Project Genesis — sculptural plaster master, raw coal. Blender 4.5 LTS.
# Candidate geometry only; compare against prior approved concepts before acceptance.
import bpy, math, random, json
from mathutils import Vector
from mathutils.noise import multi_fractal, noise_vector, noise
from pathlib import Path
random.seed(2801)
OUT=Path("output_coal_plaster_v001"); OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=7, radius=1)
obj=bpy.context.object; obj.name="Coal_Master_WhitePlaster"
obj.scale=(1.20,.79,.93)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
mesh=obj.data
for vertex in mesh.vertices:
    p=vertex.co.copy()
    # Interleaved strata and asymmetric macro silhouette, with nested fractures.
    broad=noise(p*1.18)
    irregular=noise(p*2.9)*.11
    fine=noise(p*17.3)*.017
    lamina=math.sin(p.z*11.5+p.x*1.9+noise(p*2.1)*1.5)
    layer=-.055 if lamina < -.51 else .026 if lamina > .72 else 0
    coarse=(round((p.z+noise(p*1.5)*.08)*6)/6-(p.z+noise(p*1.5)*.08))*.17
    displacement=.19*broad+irregular+fine+layer+coarse
    vertex.co=p+(p.normalized() * displacement)
    # Flatten several distinct cleavage planes, preserving a non-rounded silhouette.
    v=vertex.co
    for normal,offset,strength in [((.82,.31,.48),.89,.62), ((-.45,.72,.53),.82,.68),((.1,-.43,.9),.77,.48)]:
        n=Vector(normal).normalized()
        d=v.dot(n)-offset
        if d>0: v-=n*d*strength
    vertex.co=v
for polygon in mesh.polygons: polygon.use_smooth=False
mat=bpy.data.materials.new("Clay_WhitePlaster_NoTextures"); mat.diffuse_color=(.76,.745,.71,1)
mat.use_nodes=True
bs=mat.node_tree.nodes.get("Principled BSDF")
bs.inputs["Base Color"].default_value=(.76,.745,.71,1)
bs.inputs["Roughness"].default_value=.91
obj.data.materials.append(mat)
# Save source and GLB before adding render-only stage objects.
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/"coal_plaster_master_v001.blend").resolve()))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str((OUT/"coal_plaster_master_v001.glb").resolve()),export_format='GLB',use_selection=True)
world=bpy.context.scene.world;world.color=(.18,.18,.18)
def area(name,location,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    lamp=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(lamp)
    lamp.location=location; direction=Vector((0,0,0))-lamp.location
    lamp.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
area('Key', (3,-4,6),950,4);area('Rim',(-4,2,3),850,3)
bpy.ops.object.camera_add(location=(3.0,-4.2,2.0))
cam=bpy.context.object;cam.name='ReviewCamera';bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
for name,loc in [('front',(0,-5,1.25)),('side',(5,0,1.25)),('three_quarter',(3.5,-4.2,2.2)),('rear',(0,5,1.4))]:
    cam.location=loc;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str((OUT/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
audit={'asset':'coal_plaster_master_v001','type':'real mesh','vertices':len(mesh.vertices),'faces':len(mesh.polygons),'texture_maps':0,'views':4,'status':'candidate_for_visual_review'}
(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2))
print('MASTER_DONE',audit)
