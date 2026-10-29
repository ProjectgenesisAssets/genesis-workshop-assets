# Project Genesis — Dolphin marble fountain, sculptural V001
# Public GitHub Actions ONLY. Blender 4.5.13 LTS / Cycles.
# Candidate for four-view artistic review. NEVER auto-promote to PlayCanvas.
import bpy, math, json, os, random
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.noise import noise
from math import sin, cos, pi
random.seed(1729)
OUT = Path("output_fountain_dolphin_v001")
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
r=.72+.13*mottle-.47*streak
g=.72+.12*mottle-.43*streak
b=.69+.11*mottle-.39*streak
# A warm, ancient ivory body with irregular blue-grey graphite veins.
warm=np.maximum(0,n*.22)*np.maximum(0,1-streak)
marble_rgb=np.stack((r+.04*warm,g+.026*warm,b),axis=-1)
base_img=save_tex("marble_albedo_2k",marble_rgb)
grain=np.sin(xx*2*pi*91+yy*2*pi*57)*np.cos(yy*2*pi*113)
rough=np.clip(.43+.14*n+.17*streak+.040*grain,.24,.85)
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

marble=material("MARMOL_Envejecido_Vetas_Reales",(.70,.70,.68),.51)
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
water=material("AGUA_Celeste_Mineral_Traslucida",(.18,.45,.51),.16,0,.78)
foam=material("AGUA_Espuma_Clara",(.65,.87,.88),.22,0,.84)
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
# Subtle hand-cut vertical exterior relief; not repetitive polygon spikes.
for i in range(64):
    a=2*pi*i/64
    r=1.981
    # Each low-relief capsule is fully joined visually to the curved stone.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,
        location=(r*cos(a),r*sin(a),.47))
    o=bpy.context.object;o.name="Relieve_Cuenco_%02d"%i
    o.scale=(.023,.023,.18)
    o.rotation_euler[2]=a
    o.data.materials.append(marble);parts.append(o)

# Short pedestal in the water, crowned by a helical crest holding the dolphin.
lathe("Peana_Escultura_Rocosa",[(.28,.32),(.50,.32),(.53,.40),(.46,.50),
    (.36,.61),(.29,.78),(.27,.95),(.31,1.08),(.22,1.14),(.19,1.17)],160,marble,.01)
lathe("Anillo_Remanente_Pedestal",[(.37,.49),(.48,.49),(.50,.51),(.46,.54)],128,marble,.002)

# Curvilinear, elliptic zoological sculpt, not a stack of scaled spheres.
stations=[
    ((0,.87,1.22),.055,.055),
    ((0,.79,1.37),.115,.11),
    ((0,.66,1.49),.155,.14),
    ((0,.48,1.58),.235,.215),
    ((0,.26,1.76),.31,.275),
    ((0,.06,1.97),.335,.31),
    ((0,-.15,2.13),.275,.245),
    ((0,-.32,2.24),.207,.19),
    ((0,-.49,2.26),.142,.126),
    ((0,-.63,2.23),.092,.075),
    ((0,-.76,2.18),.019,.023)]
def catmull(a,b,c,d,t):
    return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
def station(t):
    t=max(0,min(len(stations)-1-1e-7,t))
    i=int(t);f=t-i
    def row(k):
        p,rx,ry=stations[max(0,min(len(stations)-1,k))]
        return (p[0],p[1],p[2],rx,ry)
    v=[catmull(*[row(k)[m] for k in (i-1,i,i+1,i+2)],f) for m in range(5)]
    return Vector(v[:3]),max(.01,v[3]),max(.01,v[4])
dv=[];duv=[];df=[]
N=220;M=64
for i in range(N+1):
    t=(len(stations)-1)*i/N
    p,rx,rd=station(t)
    before=station(max(0,t-.025))[0];after=station(min(len(stations)-1,t+.025))[0]
    tangent=(after-before).normalized()
    n1=Vector((1,0,0))
    n2=tangent.cross(n1).normalized()
    for j in range(M):
        a=2*pi*j/M
        direction=n1*cos(a)+n2*sin(a)
        surface=p+n1*rx*cos(a)+n2*rd*sin(a)
        relief=noise(surface*18.1)*.0018+noise(surface*42.3)*.0007
        surface+=direction*relief
        dv.append(tuple(surface))
        duv.append((t/(len(stations)-1),j/M))
for i in range(N):
    for j in range(M):
        a=i*M+j;b=i*M+(j+1)%M;c=(i+1)*M+(j+1)%M;d=(i+1)*M+j
        df.append((a,b,c,d))
set_mesh("Delfin_Salto_Marmol_Escultura",dv,df,duv,marble)

# Controlled fin thickness and flowing silhouette. No flat triangles.
def fin(name,root_a,root_b,tip,thickness=.037):
    a=Vector(root_a);b=Vector(root_b);c=Vector(tip)
    mid=(a+b)*.5
    normal=(b-a).cross(c-mid).normalized()
    vv=[];uv=[];ff=[]
    R=22;C=14
    for side in (-1,1):
        for i in range(R+1):
            v=i/R;sw=(1-v)**.77
            center=mid.lerp(c,v)+Vector((0,.055*sin(pi*v),.015*sin(pi*v)))
            for j in range(C+1):
                u=j/C
                pt=center+(b-a)*(u-.5)*sw
                pt+=normal*side*thickness*(1-v)*(.8+.2*sin(pi*u))
                vv.append(tuple(pt))
                uv.append((u,v))
    layer=(R+1)*(C+1)
    for side in range(2):
        for i in range(R):
            for j in range(C):
                o=side*layer+i*(C+1)+j
                ff.append((o,o+1,o+C+2,o+C+1) if side==1 else
                          (o+C+1,o+C+2,o+1,o))
    for i in range(R):
        for j in (0,C):
            a0=i*(C+1)+j;b0=(i+1)*(C+1)+j
            ff.append((a0,b0,b0+layer,a0+layer))
    return set_mesh(name,vv,ff,uv,marble)
fin("Aleta_Dorsal_Esculpida",(0,.07,2.20),(0,.39,1.95),(0,.38,2.46),.046)
for side in (-1,1):
    fin("Aleta_Pectoral_%s"%("Izquierda" if side<0 else "Derecha"),
        (side*.20,-.02,1.94),(side*.23,.24,1.71),
        (side*.72,.56,1.52),.032)
    fin("Aleta_Caudal_%s"%("Izquierda" if side<0 else "Derecha"),
        (0,.79,1.31),(0,1.02,1.27),(side*.62,1.21,1.24),.034)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.035,
        location=(side*.195,-.34,2.32))
    eye=bpy.context.object;eye.name="Ojo_Obsidiana_%s"%side
    eye.scale=(.48,1,.75)
    eye.data.materials.append(dark);parts.append(eye)

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
tube("Conducto_Boca_Delfin",[(0,-.74,2.18),(0,-.81,2.16)],
     [.035,.031],patina,24)

# Circular contained water has real displaced polygons and radial impact waves.
verts=[];uv=[];faces=[]
rings=95;segments=256
impact=Vector((0,-1.24,.64))
for i in range(rings+1):
    r=1.79*i/rings
    for j in range(segments):
        a=2*pi*j/segments
        x=r*cos(a);y=r*sin(a)
        d=math.sqrt((x-impact.x)**2+(y-impact.y)**2)
        wave=.013*sin(d*32)*math.exp(-d*1.3)+.006*sin(r*21+a*6)
        verts.append((x,y,.655+wave))
        uv.append((.5+x/4,.5+y/4))
for i in range(rings):
    for j in range(segments):
        faces.append((i*segments+j,i*segments+(j+1)%segments,
                      (i+1)*segments+(j+1)%segments,(i+1)*segments+j))
set_mesh("Agua_Estanque_Superficie_Ondulante",verts,faces,uv,water)

# Jet follows a high natural ballistic arc, anchored in the open mouth.
p0=Vector((0,-.80,2.16));pc=Vector((0,-1.37,2.13));p1=Vector((0,-1.24,.66))
def ballistic(t):return p0*(1-t)**2+pc*(2*t*(1-t))+p1*(t*t)
jet_points=[ballistic(i/95) for i in range(96)]
jet_r=[.032*(1-i/95)**.55+.009 for i in range(96)]
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
    radius=.12+.15*k
    ring_points=[]
    for j in range(129):
        a=2*pi*j/128
        ring_points.append((radius*cos(a),-1.24+radius*sin(a),.662+.006*k))
    tube("Ondas_Circulares_Impacto_%02d"%k,ring_points,
         [.008]*len(ring_points),foam,8)
bpy.context.scene.frame_start=1
bpy.context.scene.frame_end=192
bpy.context.scene.render.fps=24
bpy.context.scene.frame_set(65)

# Save master and export only fountain meshes, never staging lights/cameras.
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/"genesis_dolphin_marble_fountain_v001.blend").resolve()))
bpy.ops.object.select_all(action="DESELECT")
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.export_scene.gltf(
    filepath=str((OUT/"genesis_dolphin_marble_fountain_v001.glb").resolve()),
    export_format="GLB",use_selection=True,export_animations=True,
    export_materials="EXPORT",export_texcoords=True)

# Neutral studio, four Cycles beauty views; frame 65 is the active water phase.
for o in bpy.context.selected_objects:o.select_set(False)
world=bpy.context.scene.world
world.color=(.20,.22,.24)
world.use_nodes=True
bg=world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value=(.26,.31,.34,1)
bg.inputs["Strength"].default_value=.55
def area(name,location,power,size):
    data=bpy.data.lights.new(name,"AREA")
    data.energy=power;data.shape="DISK";data.size=size
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector((0,0,1.1))-obj.location).to_track_quat("-Z","Y").to_euler()
area("Key_soft", (3,-4,6),1450,5)
area("Rim_soft",(-4,2,5),1700,4)
area("Front_bounce",(-2,-5,2),400,3)
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
    "detail":((2.45,-3.4,3.12),(0,-.27,1.98)),
}
for name,(loc,target) in views.items():
    cam.location=loc
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=str((OUT/(name+".png")).resolve())
    bpy.ops.render.render(write_still=True)

meshes=[o for o in parts if o.type=="MESH"]
triangles=sum(sum(max(1,len(f.vertices)-2) for f in o.data.polygons) for o in meshes)
audit={
    "asset":"PG_PLAZA_FUENTE_DELFIN_MARMOL_V001",
    "status":"UNAPPROVED_CANDIDATE_VISUAL_QA",
    "blender_target":"4.5.13 LTS",
    "size_m":{"diameter":4.26,"height":2.46},
    "objects":len(parts),"mesh_objects":len(meshes),
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
print("GENESIS_FOUNTAIN_V001_COMPLETE",json.dumps(audit))
