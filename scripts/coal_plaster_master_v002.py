# Project Genesis — sculptural plaster master, raw coal. Blender 4.5 LTS.
# Candidate geometry only; compare against prior approved concepts before acceptance.
import bpy, math, random, json
from mathutils import Vector
from mathutils.noise import multi_fractal, noise_vector, noise
from pathlib import Path
random.seed(2801)
OUT=Path("output_coal_plaster_v002"); OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
# A deliberately fractured, non-spherical convex mineral hull.
# Intersect rays with 24 oriented hard cleavage planes, then cut minor grain.
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=7, radius=1)
obj=bpy.context.object; obj.name="Coal_Master_Fractured_Plaster"
mesh=obj.data
planes=[]
for i in range(28):
    z=1-2*(i+.5)/28
    angle=i*math.pi*(3-math.sqrt(5))
    n=Vector((math.sqrt(1-z*z)*math.cos(angle), math.sqrt(1-z*z)*math.sin(angle), z))
    n.z*=.91
    n.normalize()
    h=random.uniform(.78,1.05)
    planes.append((n,h))
# Broad directional cuts create actual sharp silhouette facets.
planes.extend([(Vector((0,0,1)),.83),(Vector((0,0,-1)),.93),
               (Vector((1,0,0)),1.09),(Vector((-1,0,0)),1.02)])
for vertex in mesh.vertices:
    u=vertex.co.normalized()
    radius=min(h / u.dot(n) for n,h in planes if u.dot(n)>.0001)
    p=u*radius
    p.x*=1.19;p.y*=.82;p.z*=1.01
    # Local damage on real vertices, weak enough to preserve the hard planes.
    grit=noise(p*11.1)*.014+noise(p*31.3)*.006
    # Fine thin shale-like splits through layered boundaries.
    stripe=math.sin(p.z*19+p.x*1.4+noise(p*1.7)*.8)
    fracture=-.037 if stripe < -.88 else 0
    p+=u*(grit+fracture)
    vertex.co=p
for polygon in mesh.polygons: polygon.use_smooth=False
mat=bpy.data.materials.new("White_Chalk_Fractured_Mineral"); mat.diffuse_color=(.84,.83,.80,1)
mat.use_nodes=True
bs=mat.node_tree.nodes.get("Principled BSDF")
bs.inputs["Base Color"].default_value=(.76,.745,.71,1)
bs.inputs["Roughness"].default_value=.91
obj.data.materials.append(mat)
# Save source and GLB before adding render-only stage objects.
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/"coal_plaster_master_v002.blend").resolve()))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str((OUT/"coal_plaster_master_v002.glb").resolve()),export_format='GLB',use_selection=True)
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
audit={'asset':'coal_plaster_master_v002','type':'real mesh','vertices':len(mesh.vertices),'faces':len(mesh.polygons),'texture_maps':0,'views':4,'status':'candidate_for_visual_review'}
(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2))
print('MASTER_DONE',audit)
