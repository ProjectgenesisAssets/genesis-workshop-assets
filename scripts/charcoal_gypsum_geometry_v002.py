"""Isolated v002: one charcoal-shaped fragment sculpted in neutral-grey clay for geometry QA.
Blender 4.5 LTS, deterministic, no source asset replacement. NOT a finished charcoal.
"""
import bpy, math, mathutils, random, json
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi

ROOT = Path("output_charcoal_gypsum_v002")
ROOT.mkdir(exist_ok=True)
random.seed(2801028)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, rough=0.91):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=rough
    return m

chalk=material("GEOMETRY_QA_OFFGREY_PLASTER_NOT_COAL",(0.47,0.455,0.44))
fiber=material("FRACTURE_SHADOW_CLAY",(0.36,0.355,0.35))
dark=material("STUDIO_FLOOR",(0.14,0.135,0.13))
# Local X aligns with original hardwood grain. No sphere/rock noise morphology.
segments=116
rings=76
length=0.114
radius_y=0.05
radius_z=0.047
vertices=[]
faces=[]
def hash_noise(a,b):
    return (sin(a*17.13+b*42.51)*sin(a*7.31-b*13.57)+sin(a*31.0+b*5.1)*0.33)
for i in range(rings):
    t=i/(rings-1)
    x=(t-.5)*length
    # Asymmetrical splintered-end profile; surface contours vary across X.
    end=0.89 + 0.12*sin(pi*t) + 0.058*sin(2*pi*t+0.38)
    for j in range(segments):
        ang=2*pi*j/segments
        # Longitudinal cracks: angled radial depressions run through most of the length.
        groove=0
        for center,width,depth in [(0.45,.075,.20),(1.72,.055,.14),(3.25,.092,.24),(4.85,.065,.16),(5.67,.05,.09)]:
            dist=abs((ang-center+pi)%(2*pi)-pi)
            groove+=depth*math.exp(-((dist/width)**2))*(.75+.25*sin(4*pi*t+center*3))
        long_ridges=.07*sin(13*ang+.35*sin(3*pi*t))+.035*sin(29*ang+1.1)
        fine=.022*hash_noise(i*.27,j*.44)
        chips=.038*max(0,sin(9*pi*t+ang*7)*sin(ang*17+t*21))**3
        r=max(.47,end*(1-groove+long_ridges+fine-chips))
        y=radius_y*r*cos(ang)*(1+.07*sin(3*pi*t+ang*3))
        z=radius_z*r*sin(ang)+.006*sin(2*pi*t+ang*2)
        xj=x+.0045*sin(4*ang+1.5*t)+.002*hash_noise(j*.33,i*.17)
        if i in (0,rings-1):
            xj+=(-1 if i==0 else 1)*.009*(.5+abs(hash_noise(j*.15,2))*.43)
        vertices.append((xj,y,z))
for i in range(rings-1):
    for j in range(segments):
        a=i*segments+j
        b=i*segments+(j+1)%segments
        faces.append((a,b,b+segments,a+segments))
# Both ends closed with cracked, stepped end-grain instead of flat caps.
for end_i,flip in [(0,True),(rings-1,False)]:
    start=len(vertices)
    for j in range(segments):
        x,y,z=vertices[end_i*segments+j]
        vertices.append((x+(.007 if flip else -.007),y*.52,z*.52))
        for j in range(segments):
        k=(j+1)%segments
        outer0=end_i*segments+j;outer1=end_i*segments+k
        inner0=start+j;inner1=start+k
        faces.append((outer1,outer0,inner0,inner1) if flip else (outer0,outer1,inner1,inner0))
    # One polygonal end surface avoids triangle-fan pinching at the central vertex.
    cap=[start+j for j in range(segments)]
    faces.append(tuple(reversed(cap)) if flip else tuple(cap))

mesh=bpy.data.meshes.new("actual_irregular_fibrous_silhouette")
mesh.from_pydata(vertices,[],faces)
mesh.update()
chunk=bpy.data.objects.new("ONE_HANDSIZED_CHARCOAL_FRAGMENT_CLAY_TEST",mesh)
bpy.context.collection.objects.link(chunk)
chunk.data.materials.append(chalk)
chunk.data.materials.append(fiber)
for polygon in chunk.data.polygons: polygon.use_smooth=(len(polygon.vertices)==4)

# Small splinter sheets follow axial grain, emerging from broken edges. Geometry, not bump map.
splinter_count=0
for n in range(17):
    a=random.uniform(0,2*pi)
    x0=random.uniform(-.049,.035)
    x1=min(.065,x0+random.uniform(.014,.044))
    j=int(a/(2*pi)*segments)%segments
    k=int((x0/length+.5)*(rings-1))
    k=max(0,min(rings-1,k))
    base=Vector(vertices[k*segments+j])
    outward=Vector((0,cos(a)*.009,sin(a)*.009))
    perp=Vector((0,-sin(a),cos(a)))
    width=random.uniform(.002,.006)
    length2=x1-x0
    origin=Vector((x0,base.y,base.z))
    corners=[origin-perp*width,
             origin+perp*width,
             origin+perp*(width*.37)+Vector((length2,0,0))+outward,
             origin-perp*(width*.31)+Vector((length2,0,0))+outward]
    fibmesh=bpy.data.meshes.new(f"fiber_split_{n:02d}")
    fibmesh.from_pydata([tuple(v) for v in corners],[],[(0,1,2,3)])
    fibmesh.update()
    obj=bpy.data.objects.new(f"FIBER_{n:02d}",fibmesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(fiber)
    solid=obj.modifiers.new("actual_fiber_sheet_thickness","SOLIDIFY")
    solid.thickness=.0011
    splinter_count+=1

# Neutral floor and 3-point studio: white geometry needs strong readable shadow.
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.081))
floor=bpy.context.object
floor.name="STUDIO_ONLY"
floor.data.materials.append(dark)
def light(name,location,power,size):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    ob=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(ob)
    ob.location=location
    ob.rotation_euler=(Vector((0,0,0))-ob.location).to_track_quat('-Z','Y').to_euler()

light("Key_softbox",(-.27,-.30,.32),45,.38)
light("Rim_light",(.27,.23,.28),25,.30)
light("Fill",(0,.35,.25),13,.38)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=72
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=-0.45
scene.render.resolution_x=1100
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=True
scene.world.color=(.055,.055,.055)
camera_data=bpy.data.cameras.new('ReviewCamera')
cam=bpy.data.objects.new('ReviewCamera',camera_data)
bpy.context.collection.objects.link(cam)
scene.camera=cam
camera_data.type='ORTHO'
camera_data.ortho_scale=.205
def render(view,location):
    cam.location=location
    aim=Vector((0,0,-.002))
    cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(ROOT/f"{view}.png")
    bpy.ops.render.render(write_still=True)
render("clay_three_quarter",(.25,-.28,.23))
render("clay_side",(0,-.40,.12))
render("clay_end",(.41,-.05,.10))

# Export just editable geometry; stage props excluded.
for ob in bpy.context.selected_objects:ob.select_set(False)
for ob in bpy.data.objects:
    ob.select_set(ob==chunk or ob.name.startswith("FIBER_"))
bpy.context.view_layer.objects.active=chunk
bpy.ops.export_scene.gltf(filepath=str(ROOT/"charcoal_gypsum_fragment_v002.glb"),export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"charcoal_gypsum_fragment_v002.blend"))
manifest={
 "asset":"blacksmith_charcoal","stage":"geometry_clay_only","version":"V002",
 "disposition":"CANDIDATE_NOT_APPROVED","dimensions_m":[.114,.100,.094],
 "workflow":"axial fibrous mesh + split fiber sheets; neutral-grey clay for silhouette inspection",
 "base_mesh_verts":len(vertices),"base_mesh_faces":len(faces),
 "splinter_sheets":splinter_count,
 "renders":["clay_three_quarter.png","clay_side.png","clay_end.png"],
 "caution":"Grey-only diagnostic. Do NOT treat as finished charcoal or apply to PlayCanvas."
}
(ROOT/"audit.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print("CHARCOAL_CLAY_GEOMETRY_V002",json.dumps(manifest))
