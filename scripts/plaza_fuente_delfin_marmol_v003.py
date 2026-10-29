# Project Genesis — Dolphin marble fountain, sculptural V003 (anatomy and material revision)
# Public GitHub Actions ONLY. Blender 4.5.13 LTS / Cycles.
# Candidate for four-view artistic review. NEVER auto-promote to PlayCanvas.
import bpy, math, json, os, random
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.noise import noise
from math import sin, cos, pi
random.seed(1729)
OUT = Path("output_fountain_dolphin_v003")
OUT.mkdir(parents=True, exist_ok=True)
TEX = OUT/"textures"
TEX.mkdir(exist_ok=True)
S = int(os.environ.get("GENESIS_TEX_SIZE","2048"))
S = max(1024, min(4096, S))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def material(name, color, rough=.5, metallic=0, alpha=1):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    b=mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*color,alpha)
    b.inputs["Roughness"].default_value=rough
    b.inputs["Metallic"].default_value=metallic
    b.inputs["Alpha"].default_value=alpha
    mat.diffuse_color=(*color,alpha)
    if alpha<1:
        try: mat.surface_render_method="DITHERED"
        except Exception: pass
        try: mat.blend_method="BLEND"
        except Exception: pass
    return mat

def save_tex(name, rgb, noncolor=False):
    rgb=np.clip(rgb,0,1).astype(np.float32)
    rgba=np.empty((S,S,4),dtype=np.float32)
    rgba[:,:,:3]=rgb
    rgba[:,:,3]=1
    img=bpy.data.images.new(name,width=S,height=S,alpha=True)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw=str((TEX/(name+".png")).resolve())
    img.file_format="PNG"
    img.save()
    if noncolor: img.colorspace_settings.name="Non-Color"
    return img

# Separate, UV-mapped physical images: irregular graphite/calcite veins, pores,
# weathered gloss and micro-normal. No color-only pseudo material.
coords=np.linspace(0,1,S,endpoint=False,dtype=np.float32)
xx,yy=np.meshgrid(coords,coords)
w=(.080*np.sin(2*pi*(3.2*xx+1.7*yy))
  +.046*np.cos(2*pi*(7.3*yy-2.4*xx))
  +.024*np.sin(2*pi*(13.0*xx+10.1*yy))
  +.012*np.cos(2*pi*(29.1*xx-17.3*yy)))
n=(.50*np.sin(2*pi*(3.4*xx+4.8*yy))
  +.29*np.cos(2*pi*(9.1*xx-3.9*yy))
  +.13*np.sin(2*pi*(27*xx+22*yy))
  +.08*np.cos(2*pi*(61*xx-55*yy)))
q=xx*5.9+yy*1.25+w*3.8+.035*n
vein=np.exp(-(np.sin(2*pi*q)/.11)**2)
secondary=np.exp(-(np.sin(2*pi*(q*1.97+yy*.53+.08*n))/.07)**2)*.38
streak=np.clip(vein*.84+secondary,.0,1)
mottle=np.clip(.53+.16*n+.15*np.sin(2*pi*(xx*2.2-yy*2.7+w)),0,1)
# Calcite marble: muted veining and mottling, physically stone-grey rather than marker lines.
r=.59+.115*mottle-.15*streak
g=.59+.110*mottle-.165*streak
b=.57+.100*mottle-.17*streak
# A warm, ancient ivory body with irregular blue-grey graphite veins.
warm=np.maximum(0,n*.22)*np.maximum(0,1-streak)
marble_rgb=np.stack((r+.04*warm,g+.026*warm,b),axis=-1)
base_img=save_tex("marble_albedo_2k",marble_rgb)
grain=np.sin(xx*2*pi*91+yy*2*pi*57)*np.cos(yy*2*pi*113)
rough=np.clip(.53+.10*n+.12*streak+.042*grain,.40,.86)
rough_img=save_tex("marble_roughness_2k",np.repeat(rough[:,:,None],3,axis=2),True)
height=(.46+.09*n-.10*streak+.035*grain).astype(np.float32)
gy,gx=np.gradient(height)
# Tangent-space RGB normal, with subdued height: no blocky pixel relief.
normx=np.clip(-gx*2.0,-.65,.65)
normy=np.clip(-gy*2.0,-.65,.65)
normz=1/np.sqrt(1+normx**2+normy**2)
normal_rgb=np.stack((.5+.5*normx*normz,.5+.5*normy*normz,.5+.5*normz),axis=-1)
normal_img=save_tex("marble_normal_2k",normal_rgb,True)
save_tex("marble_height_2k",np.repeat(height[:,:,None],3,axis=2),True)
del xx,yy,n,w,q,vein,secondary,streak,grain,marble_rgb,normal_rgb

marble=material("MARMOL_Calcita_Gris_PBR_Sobrio",(.65,.65,.62),.58)
nodes=marble.node_tree.nodes
links=marble.node_tree.links
bs=nodes.get("Principled BSDF")
for label,img,location in [
    ("Albedo_RGB",base_img,(-650,250)),
    ("Roughness_NonColor",rough_img,(-650,-40)),
    ("Tangent_Normal_NonColor",normal_img,(-650,-320))]:
    tex=nodes.new("ShaderNodeTexImage")
    tex.name=label;tex.image=img;tex.location=location
    if label=="Albedo_RGB":links.new(tex.outputs["Color"],bs.inputs["Base Color"])
    elif label=="Roughness_NonColor":
        rgb=nodes.new("ShaderNodeRGBToBW")
        rgb.location=(-370,-40)
        links.new(tex.outputs["Color"],rgb.inputs["Color"])
        links.new(rgb.outputs["Val"],bs.inputs["Roughness"])
    else:
        nm=nodes.new("ShaderNodeNormalMap")
        nm.location=(-310,-290);nm.inputs["Strength"].default_value=.7
        links.new(tex.outputs["Color"],nm.inputs["Color"])
        links.new(nm.outputs["Normal"],bs.inputs["Normal"])
water=material("AGUA_Transparente_Verdes_Pizarra",(.095,.30,.36),.09,0,.62)
foam=material("AGUA_Espuma_Sutil",(.47,.69,.70),.16,0,.70)
dark=material("PIEDRA_Ojos_Obsidiana",(.055,.068,.075),.24)
patina=material("PIEDRA_Sombras_Grabados",(.16,.20,.20),.76)

parts=[]
def set_mesh(name,verts,faces,uv=None,mat=None):
    mesh=bpy.data.meshes.new(name+"_Mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    if mat:mesh.materials.append(mat)
    if uv:
        layer=mesh.uv_layers.new(name="UV_PBR")
        for p in mesh.polygons:
            for li in p.loop_indices:
                layer.data[li].uv=uv[mesh.loops[li].vertex_index]
    for p in mesh.polygons:p.use_smooth=True
    parts.append(obj)
    return obj

def lathe(name,profile,steps=256,mat=marble,distort=0):
    vs=[];uv=[];faces=[]
    count=len(profile)
    for i,(r,z) in enumerate(profile):
        for j in range(steps):
            a=2*pi*j/steps
            rr=r+distort*(.5*sin(a*13+i*.71)+.22*sin(a*43+i*.33))
            zz=z+distort*.16*sin(a*31+i*.57)
            vs.append((rr*cos(a),rr*sin(a),zz))
            uv.append((j/steps,i/max(1,count-1)))
    for i in range(count):
        k=(i+1)%count
        for j in range(steps):
            j2=(j+1)%steps
            faces.append((i*steps+j,i*steps+j2,k*steps+j2,k*steps+j))
    return set_mesh(name,vs,faces,uv,mat)

# 4.25 m wide carved stone basin with visibly hollow inside, a thick rolled lip,
# interior slope, raised foot and an old irregular weathered edge.
basin_profile=[
    (.20,.23),(.65,.23),(1.30,.24),(1.57,.30),(1.70,.43),
    (1.77,.57),(1.79,.74),(1.87,.85),(1.99,.90),(2.10,.88),
    (2.13,.80),(2.08,.72),(2.03,.67),(1.99,.52),
    (1.91,.32),(1.76,.21),(1.45,.14),(.60,.14),(.20,.17)]
lathe("Cuenco_Marmol_Tallado_Interior_Real",basin_profile,320,marble,.006)
lathe("Zocalo_Inferior_Torneado",[(1.44,.04),(1.64,.04),
        (1.70,.08),(1.68,.16),(1.55,.18),(1.43,.15)],256,marble,.004)
lathe("Moldura_Borde_Superior",[(1.995,.84),(2.07,.85),
        (2.105,.88),(2.08,.91),(2.02,.91)],256,marble,.003)
# V003: removed repeated protruding icicles/spikes. The polished, chipped
# lip and layered carved wall profiles now read as architectural masonry.

# Short pedestal in the water, crowned by a helical crest holding the dolphin.
lathe("Peana_Escultura_Rocosa",[(.28,.32),(.50,.32),(.53,.40),(.46,.50),
    (.36,.61),(.29,.78),(.27,.95),(.31,1.08),(.22,1.14),(.19,1.17)],160,marble,.01)
lathe("Anillo_Remanente_Pedestal",[(.37,.49),(.48,.49),(.50,.51),(.46,.54)],128,marble,.002)

# Curvilinear, elliptic zoological sculpt, not a stack of scaled spheres.
# A researched, proportionally correct CC0 dolphin mesh replaces the simplistic
# V001/V002 tube sculpt. Its real UVs and surface topology remain intact.
# Original: Innerscene Common bottlenose dolphin, public domain / CC0.
# https://www.innerscene.com/tools/library/3d-parts/common-bottlenose-dolphin-a7f74d0e
source=Path("inputs/common-bottlenose-dolphin.glb")
assert source.is_file() and source.stat().st_size>100000, "Missing CC0 source dolphin"
from mathutils import Matrix
before=set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
imported=[o for o in bpy.data.objects if o.name not in before and o.type=="MESH"]
assert imported, "No dolphin geometry imported"
# Flatten glTF hierarchy safely while preserving exact imported world transforms.
for o in imported:
    world_matrix=o.matrix_world.copy()
    o.parent=None
    o.matrix_world=world_matrix
bpy.context.view_layer.update()
points=[o.matrix_world @ vert.co for o in imported for vert in o.data.vertices]
mins=Vector((min(p[i] for p in points) for i in range(3)))
maxs=Vector((max(p[i] for p in points) for i in range(3)))
bounds=maxs-mins
center=(mins+maxs)*.5
major=max(range(3),key=lambda a:bounds[a])
assert max(bounds)>1.0, "Unexpected dolphin source scale"
# Orient the long axis from tail behind to snout forward, then pitch a leaping
# dolphin so the head is high and the caudal flukes join the water-crest support.
yaw=-pi/2 if major==0 else (pi if major==1 else -pi/2)
rotate=Matrix.Rotation(-.38,4,"X") @ Matrix.Rotation(yaw,4,"Z")
scale=2.15/max(bounds)
transform=(Matrix.Translation(Vector((0,-.01,1.88))) @ rotate @
           Matrix.Scale(scale,4) @ Matrix.Translation(-center))
for o in imported:
    o.matrix_world=transform @ o.matrix_world
    for mat in list(o.data.materials):
        pass
    o.data.materials.clear()
    o.data.materials.append(marble)
    o.name="DELFIN_ESCULPIDO_CC0_ADAPTADO_"+o.name[:30]
    parts.append(o)
# Preserve a concise provenance receipt alongside the canonical candidate.
(OUT/"PROVENANCE.json").write_text(json.dumps({
    "base_model":"Common bottlenose dolphin",
    "creator":"Innerscene",
    "license":"CC0 Public Domain",
    "source":"https://www.innerscene.com/tools/library/3d-parts/common-bottlenose-dolphin-a7f74d0e",
    "download":"https://www.innerscene.com/api/library/common-bottlenose-dolphin-a7f74d0e/download",
    "modified_by":"Project Genesis fountain sculpt pipeline",
    "modifications":"scaled, pitched, retextured with original marble PBR, integrated into a new water fountain",
    "source_mesh_count":len(imported),
    "source_bounds_m":list(bounds),
    "scaled_statue_length_m":2.15
},indent=2),encoding="utf-8")

# Narrow mouth / functional stone nozzle seated in the beak.
def tube(name,points,radii,mat,segments=16):
    verts=[];uv=[];faces=[]
    for i,p in enumerate(points):
        center=Vector(p)
        prior=Vector(points[max(i-1,0)])
        after=Vector(points[min(i+1,len(points)-1)])
        tan=(after-prior).normalized()
        xaxis=Vector((1,0,0));baxis=tan.cross(xaxis).normalized()
        for j in range(segments):
            ang=2*pi*j/segments
            v=center+radii[i]*(xaxis*cos(ang)+baxis*sin(ang))
            verts.append(tuple(v))
            uv.append((i/max(1,len(points)-1),j/segments))
    for i in range(len(points)-1):
        for j in range(segments):
            faces.append((i*segments+j,i*segments+(j+1)%segments,
                          (i+1)*segments+(j+1)%segments,(i+1)*segments+j))
    return set_mesh(name,verts,faces,uv,mat)
tube("Conducto_Boca_Delfin",[(0,-.965,2.265),(0,-1.045,2.257)],
     [.022,.022],patina,20)
# Massed stone wave structurally rises from the central pedestal, bends aft
# and meets the low caudal root; the sculpture is not left unsupported.
tube("Ola_Soporte_Escultorica",
     [(0,-.03,1.095),(0,.04,1.19),(0,.19,1.31),
      (0,.43,1.45),(0,.69,1.51),(0,.91,1.49)],
     [.245,.238,.190,.142,.098,.055],marble,32)
for side in (-1,1):
    fin("Cresta_Ola_Tallada_%s"%side,
        (side*.15,.02,1.18),(side*.16,.31,1.24),
        (side*.36,.41,1.60),.024)

# Circular contained water has real displaced polygons and radial impact waves.
verts=[];uv=[];faces=[]
rings=95;segments=256
impact=Vector((0,-1.49,.64))
for i in range(rings+1):
    r=1.79*i/rings
    for j in range(segments):
        a=2*pi*j/segments
        x=r*cos(a);y=r*sin(a)
        d=math.sqrt((x-impact.x)**2+(y-impact.y)**2)
        wave=.008*sin(d*28)*math.exp(-d*1.8)+.003*sin(r*17+a*5)
        verts.append((x,y,.655+wave))
        uv.append((.5+x/4,.5+y/4))
for i in range(rings):
    for j in range(segments):
        faces.append((i*segments+j,i*segments+(j+1)%segments,
                      (i+1)*segments+(j+1)%segments,(i+1)*segments+j))
set_mesh("Agua_Estanque_Superficie_Ondulante",verts,faces,uv,water)

# Jet follows a high natural ballistic arc, anchored in the open mouth.
p0=Vector((0,-1.045,2.257));pc=Vector((0,-1.69,2.23));p1=Vector((0,-1.49,.66))
def ballistic(t):return p0*(1-t)**2+pc*(2*t*(1-t))+p1*(t*t)
jet_points=[ballistic(i/95) for i in range(96)]
jet_r=[.017*(1-i/95)**.55+.006 for i in range(96)]
jet=tube("Anim_AGUA_Chorro_Principal",jet_points,jet_r,water,16)
# Origin at mouth: scale animation emerges spatially from the dolphin, not from world zero.
for v in jet.data.vertices:v.co-=p0
jet.location=p0
for frame,scale in [(1,0.0001),(26,.0001),(37,1),(91,1),(105,.0001),(192,.0001)]:
    jet.scale=(scale,scale,scale)
    jet.keyframe_insert(data_path="scale",frame=frame,group="Escupitajo_8s")
for i in range(11):
    t0=32+i*5
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1)
    drop=bpy.context.object
    drop.name="Anim_Gota_%02d"%i
    drop.data.materials.append(foam if i%4==0 else water)
    parts.append(drop)
    for frame,t,sz in [(1,0,0),(t0-1,0,0),(t0,.02,.022),
                        (t0+8,.25,.030),(t0+17,.57,.023),
                        (t0+28,.97,.018),(t0+30,1,0),(192,1,0)]:
        drop.location=ballistic(t)+Vector((.013*sin(i*3.7),
            0,.012*sin(i*1.3+t*19)))
        drop.scale=(sz,sz*.85,sz*1.38)
        drop.keyframe_insert(data_path="location",frame=frame,group="Gotas")
        drop.keyframe_insert(data_path="scale",frame=frame,group="Gotas")
for k in range(4):
    radius=.08+.12*k
    ring_points=[]
    for j in range(129):
        a=2*pi*j/128
        ring_points.append((radius*cos(a),-1.49+radius*sin(a),.662+.004*k))
    tube("Ondas_Circulares_Impacto_%02d"%k,ring_points,
         [.004]*len(ring_points),foam,8)
bpy.context.scene.frame_start=1
bpy.context.scene.frame_end=192
bpy.context.scene.render.fps=24
bpy.context.scene.frame_set(65)

# Save master and export only fountain meshes, never staging lights/cameras.
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/"genesis_dolphin_marble_fountain_v003.blend").resolve()))
bpy.ops.object.select_all(action="DESELECT")
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.export_scene.gltf(
    filepath=str((OUT/"genesis_dolphin_marble_fountain_v003.glb").resolve()),
    export_format="GLB",use_selection=True,export_animations=True,
    export_materials="EXPORT",export_texcoords=True)

# Neutral studio, four Cycles beauty views; frame 65 is the active water phase.
for o in bpy.context.selected_objects:o.select_set(False)
world=bpy.context.scene.world
world.color=(.20,.22,.24)
world.use_nodes=True
bg=world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value=(.18,.20,.22,1)
bg.inputs["Strength"].default_value=.38
def area(name,location,power,size):
    data=bpy.data.lights.new(name,"AREA")
    data.energy=power;data.shape="DISK";data.size=size
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector((0,0,1.1))-obj.location).to_track_quat("-Z","Y").to_euler()
area("Key_soft", (3,-4,6),1120,5)
area("Rim_soft",(-4,2,5),1000,4)
area("Front_bounce",(-2,-5,2),240,3)
bpy.ops.object.camera_add()
cam=bpy.context.object;cam.name="CAMERA_QA"
scene=bpy.context.scene;scene.camera=cam
scene.render.engine="CYCLES"
scene.cycles.samples=40
scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=True
scene.view_settings.view_transform="AgX"
views={
    "front":((0,-7.5,3.40),(0,0,1.13)),
    "three_quarter":((5.7,-6.4,3.5),(0,0,1.2)),
    "side":((7,0,2.9),(0,0,1.17)),
    "detail":((2.8,-3.6,3.0),(0,-.38,2.04)),
}
for name,(loc,target) in views.items():
    cam.location=loc
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=str((OUT/(name+".png")).resolve())
    bpy.ops.render.render(write_still=True)

meshes=[o for o in parts if o.type=="MESH"]
triangles=sum(sum(max(1,len(f.vertices)-2) for f in o.data.polygons) for o in meshes)
audit={
    "asset":"PG_PLAZA_FUENTE_DELFIN_MARMOL_V003",
    "status":"UNAPPROVED_CANDIDATE_VISUAL_QA_CC0_ANATOMICAL_BASE",
    "blender_target":"4.5.13 LTS",
    "size_m":{"diameter":4.26,"height":2.46},
    "objects":len(parts),"mesh_objects":len(meshes),
    "provenance_file":"PROVENANCE.json",
    "total_triangles_including_ornament_and_water":triangles,
    "texture_resolution":S,"separate_pbr_maps":["albedo","roughness","normal","height"],
    "animation":{"name":"Escupitajo_8s","fps":24,"frames":192,
                 "onset_frame":26,"active_frames":[37,91],
                 "offset_frame":105,"loop_seconds":8,
                 "note":"PlayCanvas must loop exported animation clip; no fluid simulation dependency"},
    "review_views":list(views),"engine":"Cycles CPU",
    "acceptance":"Gabriel approval after actual 4-view review and >=8/10",
}
(OUT/"AUDIT.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
print("GENESIS_FOUNTAIN_V003_COMPLETE",json.dumps(audit))
