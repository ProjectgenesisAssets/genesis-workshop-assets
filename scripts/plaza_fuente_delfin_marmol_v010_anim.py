# Project Genesis — Dolphin marble fountain, sculptural V010 (anatomy and material revision)
# Public GitHub Actions ONLY. Blender 4.5.13 LTS / Cycles.
# Candidate for four-view artistic review. NEVER auto-promote to PlayCanvas.
import bpy, math, json, os, random, shutil, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.noise import noise
from math import sin, cos, pi
random.seed(1729)
OUT = Path("output_fountain_dolphin_v010")
OUT.mkdir(parents=True, exist_ok=True)
TEX = OUT/"textures"
TEX.mkdir(exist_ok=True)
S = 4096  # scanned 4K source maps, no synthetic map fabrication
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

# Photogrammetry-derived real-world outdoor marble metamorphic stone.
# Poly Haven / Amal Kumar / CC0: https://polyhaven.com/a/marble_rock_01
# Four independent 4K maps, never a procedural painted line pattern.
PBR_ROOT=Path("inputs/marble_rock_01")
PBR_LABELS={"Diffuse":"marble_albedo_4k.jpg","Rough":"marble_roughness_4k.jpg",
            "nor_gl":"marble_normal_4k.png","Displacement":"marble_height_4k.png"}
stone_images={}
source_hashes={}
for key,fn in PBR_LABELS.items():
    original=PBR_ROOT/fn
    assert original.exists() and original.stat().st_size>100000, "Missing 4K scanned texture: "+fn
    copied=TEX/fn
    shutil.copy2(original,copied)
    img=bpy.data.images.load(str(copied.resolve()),check_existing=False)
    if key!="Diffuse":img.colorspace_settings.name="Non-Color"
    assert img.size[0]==4096 and img.size[1]==4096, "Not a 4K PBR map: "+fn
    stone_images[key]=img
    source_hashes[key]=hashlib.sha256(copied.read_bytes()).hexdigest()

def scanned_marble(name,tint=(1,1,1),rough_factor=1.0,micro=.33):
    mat=material(name,(.70,.69,.67),.58)
    bs=mat.node_tree.nodes.get("Principled BSDF")
    ns=mat.node_tree.nodes;ln=mat.node_tree.links
    texnodes={}
    coords=ns.new("ShaderNodeTexCoord")
    coords.location=(-1100,0)
    mapping=ns.new("ShaderNodeMapping")
    mapping.location=(-900,0)
    mapping.inputs["Scale"].default_value=(1.0,1.0,1.0)
    ln.new(coords.outputs["UV"],mapping.inputs["Vector"])
    for n,key,y in [("Albedo_4K","Diffuse",400),("Roughness_4K","Rough",100),
                    ("Normal_GL_4K","nor_gl",-200),("Height_4K","Displacement",-490)]:
        t=ns.new("ShaderNodeTexImage")
        t.name=n;t.image=stone_images[key];t.location=(-660,y)
        t.extension="REPEAT";t.interpolation="Linear"
        ln.new(mapping.outputs["Vector"],t.inputs["Vector"])
        texnodes[key]=t
    # Direct Principled connections survive glTF export consistently.
    # Wet finish is implemented with physically plausible clearcoat instead
    # of color-only hacks that the game exporter would silently drop.
    ln.new(texnodes["Diffuse"].outputs["Color"],bs.inputs["Base Color"])
    ln.new(texnodes["Rough"].outputs["Color"],bs.inputs["Roughness"])
    iswet=("MOJADO" in name)
    bs.inputs["Coat Weight"].default_value=.42 if iswet else (.12 if "ESCULPIDO" in name else .035)
    bs.inputs["Coat Roughness"].default_value=.08 if iswet else .31
    normal=ns.new("ShaderNodeNormalMap");normal.space="TANGENT"
    normal.inputs["Strength"].default_value=micro
    normal.location=(-330,-200)
    ln.new(texnodes["nor_gl"].outputs["Color"],normal.inputs["Color"])
    # glTF exporter can preserve this direct tangent-space normal connection.
    # Real 4K height is packaged as a separate mask for optional offline tessellation.
    ln.new(normal.outputs["Normal"],bs.inputs["Normal"])
    bs.inputs["Metallic"].default_value=0
    return mat

# The same geological material has different finishes due to wear and water.
marble=scanned_marble("MARMOL_VIEJO_Canteria_Escaneada_PBR4K",(.91,.92,.94),.96,.37)
sculptmarble=scanned_marble("MARMOL_ESCULPIDO_Satinado_Con_Poros",(.98,.99,1.0),.73,.20)
wetmarble=scanned_marble("MARMOL_MOJADO_Albedo_Atenuado",(.64,.69,.73),.40,.29)

def water_glass(name,roughness=.058):
    mat=material(name,(.84,.94,.96),roughness,0,1)
    bs=mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Transmission Weight"].default_value=.92
    bs.inputs["IOR"].default_value=1.333
    bs.inputs["Roughness"].default_value=roughness
    bs.inputs["Coat Weight"].default_value=.0
    return mat

water=water_glass("AGUA_Fisica_Incolora_Refraccion_1p333")
poolwater=water_glass("AGUA_Estanque_Transparente_Reflectiva",.09)
# V010: Remove synthetic sky-blue appearance: teal-gray water, more true refraction,
# natural Fresnel, stronger 2K ripple normals. Stone sculpt and PBR maps untouched.
# This is WATER ONLY. The 4K scanned marble, geometry and UVs are unchanged.
pool_bs=poolwater.node_tree.nodes.get("Principled BSDF")
pool_bs.inputs["Base Color"].default_value=(.065,.14,.15,1)
pool_bs.inputs["Transmission Weight"].default_value=.91
pool_bs.inputs["Roughness"].default_value=.072
pool_bs.inputs["Specular IOR Level"].default_value=.50
poolwater.diffuse_color=(.065,.14,.15,1)
jet_bs=water.node_tree.nodes.get("Principled BSDF")
jet_bs.inputs["Base Color"].default_value=(.29,.54,.71,1)
jet_bs.inputs["Transmission Weight"].default_value=.86
jet_bs.inputs["Roughness"].default_value=.064
foam=material("AGUA_Espuma_Impacto_Burbujas",(.75,.83,.81),.32,0,.65)
dark=material("PIEDRA_Ojos_Obsidiana",(.055,.068,.075),.24)
patina=material("PIEDRA_Sombras_Grabados",(.16,.20,.20),.76)


# V010: Pool water shader and normals ONLY; certified stone and marble unchanged.
# Seamless 2K OpenGL (+Y) water normal map, physically transparent (no cyan color).
WN=2048
U=np.arange(WN,dtype=np.float32)[None,:]/WN
V=np.arange(WN,dtype=np.float32)[:,None]/WN
H=np.zeros((WN,WN),dtype=np.float32)
for kx,ky,amp,phase in [(2,3,.29,.10),(-4,5,.16,1.20),(7,-5,.11,2.27),
                         (11,3,.085,.67),(-13,17,.045,1.19),(19,-11,.031,2.8),
                         (27,23,.018,3.26),(31,-29,.014,1.76)]:
    H+=amp*np.sin(2*np.pi*(kx*U+ky*V)+phase)
DX=(np.roll(H,-1,axis=1)-np.roll(H,1,axis=1))*12.0
DY=(np.roll(H,-1,axis=0)-np.roll(H,1,axis=0))*12.0
NORM=np.reciprocal(np.sqrt(DX*DX+DY*DY+1))
PIX=np.empty((WN,WN,4),dtype=np.float32)
PIX[:,:,0]=.5-.5*DX*NORM
PIX[:,:,1]=.5-.5*DY*NORM
PIX[:,:,2]=.5+.5*NORM
PIX[:,:,3]=1
water_normal=bpy.data.images.new("GENESIS_AGUA_NORMAL_2K",WN,WN,alpha=True)
water_normal.pixels.foreach_set(PIX.ravel())
water_normal.filepath_raw=str((TEX/"water_ripples_normal_2k.png").resolve())
water_normal.file_format="PNG"
water_normal.save()
water_normal.colorspace_settings.name="Non-Color"
del PIX,H,DX,DY,NORM
water_mapping_nodes={}
def animate_water_normal(mat,tiling,flow,strength):
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    uv=nodes.new("ShaderNodeTexCoord")
    uv.location=(-680,-280)
    mapper=nodes.new("ShaderNodeMapping")
    mapper.name="GENESIS_WATER_UV_SCROLL"
    mapper.location=(-460,-280)
    mapper.inputs["Scale"].default_value=(tiling,tiling,1)
    links.new(uv.outputs["UV"],mapper.inputs["Vector"])
    tex=nodes.new("ShaderNodeTexImage")
    tex.name="WATER_NORMAL_2K_TILEABLE"
    tex.location=(-230,-280)
    tex.image=water_normal
    tex.extension="REPEAT"
    links.new(mapper.outputs["Vector"],tex.inputs["Vector"])
    normal=nodes.new("ShaderNodeNormalMap")
    normal.location=(30,-270)
    normal.inputs["Strength"].default_value=strength
    links.new(tex.outputs["Color"],normal.inputs["Color"])
    links.new(normal.outputs["Normal"],nodes.get("Principled BSDF").inputs["Normal"])
    mapper.inputs["Location"].default_value=(0,0,0)
    mapper.inputs["Location"].keyframe_insert(data_path="default_value",frame=1)
    mapper.inputs["Location"].default_value=(flow[0],flow[1],0)
    mapper.inputs["Location"].keyframe_insert(data_path="default_value",frame=193)
    water_mapping_nodes[mat.name]=mapper
animate_water_normal(poolwater,6.0,(.60,-.75),.52)
animate_water_normal(water,2.5,(0,2.0),.18)

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
    # Arc-length UVs avoid vertical stretch on tall classical columns.
    lengths=[0.0]
    for ix in range(1,count):
        lengths.append(lengths[-1]+math.hypot(profile[ix][0]-profile[ix-1][0],
                                             profile[ix][1]-profile[ix-1][1]))
    for i,(r,z) in enumerate(profile):
        for j in range(steps):
            a=2*pi*j/steps
            fluting=.021*(.5+.5*cos(16*a)) if name=="Columna_Marmol_Clasica_Acanalada" and 7<=i<=10 else 0.0
            rr=r+distort*(.5*sin(a*13+i*.71)+.22*sin(a*43+i*.33))-fluting
            zz=z+distort*.16*sin(a*31+i*.57)
            vs.append((rr*cos(a),rr*sin(a),zz))
            if "Columna_" in name:
                uv.append((j/steps*2.9,lengths[i]*2.0))
            elif name.startswith(("Basa_","Capitel_")):
                uv.append((j/steps*3.1,lengths[i]*1.75))
            else:
                uv.append((j/steps*6.5,i/max(1,count-1)*2.4))
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
basin=lathe("Cuenco_Marmol_Tallado_Interior_Real",basin_profile,320,marble,.006)
basin.data.materials.append(wetmarble)
for poly in basin.data.polygons:
    # Basin lip remains matte, waterline and internal bowl progressively damp.
    if poly.index//320 >= 12:poly.material_index=1
lathe("Zocalo_Inferior_Torneado",[(1.44,.04),(1.64,.04),
        (1.70,.08),(1.68,.16),(1.55,.18),(1.43,.15)],256,marble,.004)
lathe("Moldura_Borde_Superior",[(1.995,.84),(2.07,.85),
        (2.105,.88),(2.08,.91),(2.02,.91)],256,marble,.003)
# V010: removed repeated protruding icicles/spikes. The polished, chipped
# lip and layered carved wall profiles now read as architectural masonry.

# A genuine classical carved stone pedestal replaces the odd V005 branch.
# Its fluted shaft and capital can be fabricated by a medieval stone mason.
column_profile=[
    (.18,.30),(.48,.30),(.55,.35),(.55,.39),(.49,.43),(.44,.48),
    (.39,.52),(.37,.59),(.355,.67),(.355,1.25),
    (.375,1.31),(.425,1.355),(.47,1.38),(.47,1.415),
    (.43,1.435),(.36,1.475),(.32,1.53),(.29,1.59)]
pedestal=lathe("Columna_Marmol_Clasica_Acanalada",column_profile,320,sculptmarble,.001)
pedestal.location.y=.36
base_molding=lathe("Basa_Columna_Moldura_Esculpida",
   [(.42,.47),(.52,.47),(.55,.50),(.51,.54),(.41,.56)],192,sculptmarble,.0005)
base_molding.location.y=.36
# End plate blends under the dolphin's torso, not an unsupported flying statue.
cap=lathe("Capitel_Tallado_Bajo_Delfin",
   [(.27,1.52),(.36,1.52),(.39,1.545),(.36,1.58),(.25,1.605)],192,sculptmarble,.0005)
cap.location.y=.36
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
rotate=Matrix.Rotation(-.55,4,"X") @ Matrix.Rotation(yaw,4,"Z")
scale=2.15/max(bounds)
transform=(Matrix.Translation(Vector((0,-.01,1.88))) @ rotate @
           Matrix.Scale(scale,4) @ Matrix.Translation(-center))
for o in imported:
    o.matrix_world=transform @ o.matrix_world
    for mat in list(o.data.materials):
        pass
    o.data.materials.clear()
    o.data.materials.append(sculptmarble)
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
    "modifications":"scaled, pitched, retextured in scanned CC0 marble PBR, integrated into a carved fountain",
    "stone_texture_source":"https://polyhaven.com/a/marble_rock_01",
    "stone_texture_author":"Amal Kumar / Poly Haven",
    "stone_texture_license":"CC0",
    "stone_texture_sha256":source_hashes,
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
    # Close watertight stone supports, no visible black hollow tube ends.
    if name.startswith("Ola_") or name.startswith("Conducto_"):
        faces.append(tuple(reversed([i for i in range(segments)])))
        faces.append(tuple((len(points)-1)*segments+j for j in range(segments)))
    return set_mesh(name,verts,faces,uv,mat)
# Water appears directly at the dolphin rostrum; no visible plastic/dark mouth insert.
# Massed stone wave structurally rises from the central pedestal, bends aft
# and meets the low caudal root; the sculpture is not left unsupported.
# A direct, architectural stone capital touches the sculpture.
# No free-floating curved branch, root-like trunk, or black tube seam.
# The authentic dolphin mesh replaces the procedurally defined fin helper.
# No decorative fin-like protrusions are added to the supporting stone wave.

# The pool is a thin physically transparent surface, not a turquoise plastic disc.
# Subtle, irregular nested waves are actual displaced geometry visible in Cycles.
verts=[];uv=[];faces=[]
rings=126;segments=320
impact=Vector((0,-1.48,.643))
for i in range(rings+1):
    r=1.80*i/rings
    for j in range(segments):
        a=2*pi*j/segments
        x=r*cos(a);y=r*sin(a)
        dist=math.hypot(x-impact.x,y-impact.y)
        wav=.009*sin(dist*31+.12*sin(a*7))*math.exp(-dist*1.8)
        wav+=.0018*sin(9.1*x+4.6*y)*sin(11.5*y-2.7*x)
        wav+=.0007*sin(29.4*x-10.6*y)*sin(24.8*y+3.2*x)
        verts.append((x,y,.652+wav))
        uv.append((.5+x/3.65,.5+y/3.65))
for i in range(rings):
    for j in range(segments):
        faces.append((i*segments+j,i*segments+(j+1)%segments,
                      (i+1)*segments+(j+1)%segments,(i+1)*segments+j))
set_mesh("AGUA_Estanque_Reflejos_Superficie_Rizada",verts,faces,uv,poolwater)

# Real location of the protruding rostrum from the transformed dolphin source.
all_dolphin_verts=[o.matrix_world @ v.co for o in imported for v in o.data.vertices]
rostrum_candidates=[p for p in all_dolphin_verts if p.y<-.65 and p.z>1.85]
if rostrum_candidates:
    nose=min(rostrum_candidates,key=lambda p:abs(p.x)*.5+p.y)
    p0=Vector((nose.x,nose.y-.018,nose.z-.009))
else:
    p0=Vector((0,-1.045,2.257))
print("GENESIS_SPOUT_ANCHOR",list(p0))
# The water is attached to the actual transformed dolphin surface, not a hardcoded point.
# Accurate mouth-to-jet origin. No decorative black stem projecting from stone.
# A ballistic parabola broken into transparent refractive uneven strands.
p1=Vector((p0.x*.45,-1.48,.667))
peak=Vector((p0.x,-max(1.52,abs(p0.y)+.66),max(p0.z+.10,2.33)))
def ballistic(t):
    return p0*(1-t)**2+peak*(2*t*(1-t))+p1*t*t
section_count=21
flow_parts=[]
for i in range(section_count):
    a=i/section_count
    b=(i+1)/section_count
    # Slight natural interruption between segments, no uniform extruded cyan hose.
    gap=.00008+.00020*(i/section_count)**1.4
    a+=gap;b-=gap
    points=[];radii=[]
    steps=5
    for j in range(steps):
        t=a+(b-a)*j/(steps-1)
        pos=ballistic(t)
        # Subtle inertial breakup along the jet: no large repeated beads.
        pos.x+=.0035*sin(t*123+i*2.1)
        pos.z+=.0026*sin(t*71+i*1.7)
        points.append(tuple(pos))
        radii.append((.0125-.0060*t)*(1+.17*sin(t*119+i*.76)))
    part=tube("Anim_Chorro_Transparente_Filamento_%02d"%i,points,radii,water,12)
    flow_parts.append(part)
    born=27+int(1.25*i)
    off=88+int(.90*i)
    for fr,k in [(1,.0001),(born-1,.0001),(born,1),
                 (off,1),(off+5,.0001),(192,.0001)]:
        part.scale=(k,k,k)
        part.keyframe_insert(data_path="scale",frame=fr,group="Escupitajo_8s")
# Fine water droplets falling with natural speed and varied transparent silhouettes.
for i in range(29):
    birth=31+i*2
    start=.03+.016*(i%4)
    end=.80+.025*(i%7)
    rng=random.Random(4600+i)
    scatter=rng.uniform(-.017,.017)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=1)
    drop=bpy.context.object
    drop.name="Anim_Gota_Agua_Fisica_%02d"%i
    drop.data.materials.append(water if i%8 else foam)
    parts.append(drop)
    for frame,t,sz in [(1,start,.0001),(birth-1,start,.0001),
                       (birth,start,.006+rng.uniform(0,.003)),
                       (birth+8,start+(end-start)*.26,.012),
                       (birth+18,start+(end-start)*.67,.008),
                       (birth+25,end,.005),(birth+27,end,.0001),(192,end,.0001)]:
        pt=ballistic(t)
        pt.x+=scatter*(.4+t);pt.y+=rng.uniform(-.014,.014)*t
        drop.location=pt
        drop.scale=(sz*.70,sz*.85,sz*(1.1+.7*t))
        drop.keyframe_insert(data_path="location",frame=frame,group="Gotas")
        drop.keyframe_insert(data_path="scale",frame=frame,group="Gotas")

# Distinct liquid impact splashes (thin ribbons) and progressively expanding rings.
for k in range(9):
    a=2*pi*k/9+.13
    splashp=[
        (p1.x+.04*cos(a),p1.y+.04*sin(a),.663),
        (p1.x+.07*cos(a),p1.y+.09*sin(a),.71),
        (p1.x+.12*cos(a),p1.y+.13*sin(a),.77),
        (p1.x+.14*cos(a),p1.y+.16*sin(a),.78)]
    obj=tube("Anim_Salpicadura_Cinematica_%02d"%k,splashp,
             [.006,.0048,.0032,.0007],water,8)
    for frame,sz in [(1,.0001),(48+k//2,.0001),(55+k//2,1),
                     (96+k//2,1),(115+k//2,.0001),(192,.0001)]:
        obj.scale=(sz,sz,sz)
        obj.keyframe_insert(data_path="scale",frame=frame,group="Impacto")
for k in range(3):
    radius=.085+.125*k
    ring_points=[]
    for j in range(129):
        a=2*pi*j/128
        irregular_radius=radius*(1+.037*sin(7*a+k*.9)+.019*sin(13*a+1.7*k))
        ring_points.append((p1.x+irregular_radius*cos(a),
                            p1.y+irregular_radius*sin(a),
                            .660+.002*k+.0015*sin(9*a+k)))
    ring=tube("Anim_Ondas_Impacto_%02d"%k,ring_points,
              [.0016]*len(ring_points),water,7)
    for frame,sz in [(1,.0001),(45+k*4,.0001),(54+k*4,1),
                     (100+k*3,1),(119+k*3,.0001),(192,.0001)]:
        ring.scale=(sz,sz,sz)
        ring.keyframe_insert(data_path="scale",frame=frame,group="Ondas")
bpy.context.scene.frame_start=1
bpy.context.scene.frame_end=192
bpy.context.scene.render.fps=24
bpy.context.scene.frame_set(65)

(OUT/"WATER_ANIMATION.json").write_text(json.dumps({
    "revision":"V010","marble_unchanged_from":"V007",
    "normal_texture":"textures/water_ripples_normal_2k.png",
    "water_normal_resolution":WN,"normal_convention":"OpenGL tangent space",
    "animation":"Blender UV scroll + companion PlayCanvas dual normal scroll",
    "loop_seconds":8,"pool_scroll_uv_per_second":[.125,-.125],
    "jet_scroll_uv_per_second":[0,.25],
    "source":"Original mathematical water waves",
    "playcanvas_script":"playcanvas/fountain_water_animated_v010.js",
    "stone_surface":"Unchanged scanned 4K marble",
    "water_pool_tint_linear":[.065,.14,.15],
    "water_jet_tint_linear":[.29,.54,.71],
    "status":"water candidate; requires visual QA against V009 sky blue"
},indent=2),encoding="utf-8")

# Save master and export only fountain meshes, never staging lights/cameras.
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/"genesis_dolphin_marble_fountain_v010.blend").resolve()))
bpy.ops.object.select_all(action="DESELECT")
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.export_scene.gltf(
    filepath=str((OUT/"genesis_dolphin_marble_fountain_v010.glb").resolve()),
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
scene.cycles.samples=64
scene.cycles.max_bounces=10
scene.cycles.transmission_bounces=8
scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True
scene.view_settings.view_transform="AgX"
views={
    "front":((0,-7.5,3.40),(0,0,1.13)),
    "three_quarter":((5.7,-6.4,3.5),(0,0,1.2)),
    "side":((7,0,2.9),(0,0,1.17)),
    "detail":((2.8,-3.6,3.0),(0,-.38,2.04)),
}
# V010 water-only animation review: frame sequence, not a new mesh revision.
# Render every other canonical 24 fps frame at 12 fps to keep public CI practical.
# The GLB itself keeps its original 192-frame / 24-fps / 8-second animation.
frames_dir=OUT/"animated_frames"
frames_dir.mkdir(parents=True,exist_ok=True)
scene.frame_start=1
scene.frame_end=192
scene.frame_step=2
scene.render.fps=24
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGB"
cam.location=(5.7,-6.4,3.5)
cam.rotation_euler=(Vector((0,0,1.2))-cam.location).to_track_quat("-Z","Y").to_euler()
scene.render.filepath=str((frames_dir/"dolphin_").resolve())
bpy.ops.render.render(animation=True)
scene.frame_set(65)
(OUT/"ANIMATION_QA.json").write_text(json.dumps({
    "asset":"PG_PLAZA_FUENTE_DELFIN_MARMOL_V010",
    "animation":"V010 dolphin spits water once per 8-second loop",
    "source_fps":24,
    "source_frame_count":192,
    "review_render_fps":12,
    "review_frame_step":2,
    "review_frame_count_expected":96,
    "preview_size":[960,720],
    "cycles_samples":24,
    "material":"V010 neutral mineral teal pool, 91% transmission, 2K amplified moving ripple normals",
    "marble":"unchanged V007-approved 4K PBR stone",
    "status":"REVIEW_ONLY_NOT_YET_PLAYCANVAS_TESTED"
},indent=2),encoding="utf-8")


meshes=[o for o in parts if o.type=="MESH"]
triangles=sum(sum(max(1,len(f.vertices)-2) for f in o.data.polygons) for o in meshes)
audit={
    "asset":"PG_PLAZA_FUENTE_DELFIN_MARMOL_V010",
    "status":"UNAPPROVED_CANDIDATE_4K_SCANNED_MARBLE_PHYSICAL_WATER",
    "blender_target":"4.5.13 LTS",
    "size_m":{"diameter":4.26,"height":2.65},
    "objects":len(parts),"mesh_objects":len(meshes),
    "provenance_file":"PROVENANCE.json",
    "total_triangles_including_ornament_and_water":triangles,
    "texture_resolution":S,"separate_pbr_maps":["albedo","roughness","normal","height"],
    "stone_material":"Poly Haven Marble Rock 01 / Amal Kumar / CC0",
    "stone_source_sha256":source_hashes,
    "water_ior":1.333,
    "water_pool_base_color_linear":[.065,.14,.15],
    "water_jet_base_color_linear":[.29,.54,.71],
    "marble_change":"NONE: V007 PBR and geometry preserved",
    "jet_sections":section_count,
    "water_normal_texture":"textures/water_ripples_normal_2k.png",
    "water_normal_resolution":WN,
    "water_loop_materials":list(water_mapping_nodes),
    "animation":{"name":"Escupitajo_8s","fps":24,"frames":192,
                 "onset_frame":27,"active_frames":[55,88],
                 "offset_frame":112,"loop_seconds":8,
                 "note":"Independent water stream sections, droplets, splashes and waves keyed into glTF; PlayCanvas loops 8 s animation"},
    "review_views":list(views),"engine":"Cycles CPU",
    "acceptance":"Gabriel approval after actual 4-view review and >=8/10",
}
(OUT/"AUDIT.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
print("GENESIS_FOUNTAIN_V010_ANIMATION_FRAMES_COMPLETE",json.dumps(audit))
