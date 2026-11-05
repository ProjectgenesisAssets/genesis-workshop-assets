"""Escudo hierro de aprendiz V015: malla original Meshy, V175 y roble PBR del proyecto.
Experimento para revisión visual; no representa asset aprobado de PlayCanvas.
"""
import bpy, hashlib, json, math, random
from pathlib import Path
from mathutils import Vector

ROOT=Path.cwd()
OUT=ROOT/"output_escudo_meshy_v015"
OUT.mkdir(exist_ok=True)
SRC=ROOT/"source_assets/meshy/jajar_019871b7/escudo_original.glb"
IRON_FILE=ROOT/"input/PG_IRON_V175_WEB_WORKCOPY.blend"
HDRI=ROOT/"output_escudo_meshy_v015/studio_small_09_2k.hdr"
OAK=ROOT/"oak_pbr_v004"
OAK_FILES=("wood_albedo.jpg","wood_normal.png","wood_roughness.png")
LEATHER=ROOT/"approved_caprino_v020"
LEATHER_FILES=("leather_albedo_v020.png","leather_normal_v020.png","leather_roughness_v020.png")
LEATHER_SHA={
 "leather_albedo_v020.png":"000a561fee2d2a48ea88988f01d956ec15f1e8006c03db13e187445eaedebb26",
 "leather_normal_v020.png":"6618f354f0e8f918fe177993da133cad5a7a34cbd88c31140491e2f2506e3314",
 "leather_roughness_v020.png":"7c7fa3b77170f3cc8c19c4247620d5bb47cc9d51bf219a11571564159eb443ff"}
SRC_SHA="ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2"
IRON_SHA="8b67ec62da384fb31ad80dcc35feec7a2f1bff08e03ad80ab3205f53dd6588ba"
for f in [SRC,IRON_FILE,HDRI]+[OAK/x for x in OAK_FILES]+[LEATHER/x for x in LEATHER_FILES]:
    if not f.is_file() or f.stat().st_size<10000: raise RuntimeError("Missing genuine reference: "+str(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SRC)==SRC_SHA, "Original Meshy source changed"
assert sha(IRON_FILE)==IRON_SHA, "V175 reference changed"
for filename,expected in LEATHER_SHA.items():
    assert sha(LEATHER/filename)==expected, "Approved leather map hash mismatch: "+filename
REPORT={"version":"V015","status":"experimental_not_approved","blender":bpy.app.version_string,
        "source_meshy_sha256":sha(SRC),"source_v175_sha256":sha(IRON_FILE),
        "hdr32_sha256":sha(HDRI),"oak_source_repo":"ProjectgenesisAssets/genesis-workshop-assets",
        "oak_branch":"asset/tutorial-roble_seco",
        "oak_maps":[{"filename":f,"bytes":(OAK/f).stat().st_size,"sha256":sha(OAK/f)} for f in OAK_FILES],
        "renders":[],"approved_v020_leather_reference":{"source_GLBSHA256":"5aaeb196738d9b70cbce32102aad9ef4562b4da88550e08a2aea03ca061dca37","source_owner_approved":True,"shield_candidate_unapproved":True,"map_sha256":LEATHER_SHA}}
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SRC))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if len(meshes)!=1:raise RuntimeError("Expected original 1-mesh shield")
ob=meshes[0]
original_mat=ob.data.materials[0]
if not original_mat:raise RuntimeError("Original Meshy material absent")
if not ob.data.uv_layers:raise RuntimeError("UVs missing: cannot apply original oak maps")
REPORT["source_triangles"]=sum(len(p.vertices)-2 for p in ob.data.polygons)
REPORT["original_mesh_scale"]=list(ob.scale)
bpy.context.view_layer.objects.active=ob
bpy.ops.object.select_all(action="DESELECT");ob.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)

with bpy.data.libraries.load(str(IRON_FILE),link=False) as (source,loaded):
    if "V153_FrontOxidation_Only_MatchedBack" not in source.materials:
        raise RuntimeError("V175 procedural front iron absent")
    loaded.materials=["V153_FrontOxidation_Only_MatchedBack"]
base=loaded.materials[0]
iron=base.copy()
iron.name="Shield_V015_V175_ForgedIron_Derived"
bs=next((n for n in iron.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None)
if bs is None:raise RuntimeError("V175 metal missing PBR node")
bs.inputs["Metallic"].default_value=0.72
REPORT["iron_material"]={"from_v175":base.name,"derived":iron.name,
                        "metallic":0.72,"procedural_nodes":len(iron.node_tree.nodes)}

oak=bpy.data.materials.new("Shield_V015_Genesis_RobleSeco_V004_PBR")
oak.use_nodes=True
ns=oak.node_tree.nodes;ls=oak.node_tree.links
principled=ns.get("Principled BSDF")
principled.inputs["Metallic"].default_value=0
principled.inputs["Roughness"].default_value=.80
uv=ns.new("ShaderNodeTexCoord")
mapping=ns.new("ShaderNodeMapping")
mapping.inputs["Scale"].default_value=(1.8,1.8,1)
# Meshy UV atlas covers arbitrary islands and made the oak rim almost white.
# Reproject actual photo PBR in the shield X/Z plane in object generated coordinates.
sep=ns.new("ShaderNodeSeparateXYZ")
comb=ns.new("ShaderNodeCombineXYZ")
ls.new(uv.outputs["Generated"],sep.inputs["Vector"])
ls.new(sep.outputs["X"],comb.inputs["X"])
ls.new(sep.outputs["Z"],comb.inputs["Y"])
ls.new(comb.outputs["Vector"],mapping.inputs["Vector"])
def load_oak(filename,colorspace):
    node=ns.new("ShaderNodeTexImage")
    node.image=bpy.data.images.load(str(OAK/filename),check_existing=True)
    node.image.colorspace_settings.name=colorspace
    ls.new(mapping.outputs["Vector"],node.inputs["Vector"])
    return node
col=load_oak("wood_albedo.jpg","sRGB")
rough=load_oak("wood_roughness.png","Non-Color")
normal=load_oak("wood_normal.png","Non-Color")
norm=ns.new("ShaderNodeNormalMap")
norm.inputs["Strength"].default_value=.65
# Preserve genuine photographic grain, apply aged-oak tonal treatment rather
# than substitute a flat brown color. Multiplication retains image detail.
tint=ns.new("ShaderNodeMixRGB")
tint.blend_type="MULTIPLY"
tint.inputs[0].default_value=1
tint.inputs[2].default_value=(.24,.155,.105,1)
ls.new(col.outputs["Color"],tint.inputs[1])
ls.new(tint.outputs["Color"],principled.inputs["Base Color"])
ls.new(rough.outputs["Color"],principled.inputs["Roughness"])
ls.new(normal.outputs["Color"],norm.inputs["Color"])
ls.new(norm.outputs["Normal"],principled.inputs["Normal"])

coords=[ob.matrix_world@Vector(c) for c in ob.bound_box]
mn=[min(p[i] for p in coords) for i in range(3)]
mx=[max(p[i] for p in coords) for i in range(3)]
dm=[mx[i]-mn[i] for i in range(3)]
c=Vector([(mx[i]+mn[i])*.5 for i in range(3)])
if min(range(3),key=lambda i:dm[i])!=1:raise RuntimeError("Unknown shield axis")
R=max(dm[0],dm[2])*.5
ymn,yd=mn[1],dm[1]
# V015: the original Meshy mesh remains untouched in shape and SHA.
# Do not pretend its wooden boards become wrought metal by a grey shader.
# Original single-mesh source is a timber understructure. Re-cover front
# with a separate forged steel shell, a genuinely modelled solid oak hoop,
# and discrete iron pegs. No changes to original GLB source.
ob.data.materials[0]=oak
ob.data.materials.append(oak)
ob.data.materials.append(original_mat)
counts={"oak_understructure":0,"original_back_straps":0}
for poly in ob.data.polygons:
    p=ob.matrix_world@poly.center
    x=abs(p.x-c.x);z=abs(p.z-c.z)
    radial=math.hypot(x,z)
    strap=(p.y>ymn+0.68*yd and
           0.25*R<x<0.77*R and z<0.71*R and radial<.82*R)
    if strap:
        poly.material_index=2
        counts["original_back_straps"]+=1
    else:
        poly.material_index=1
        counts["oak_understructure"]+=1
if min(counts.values())<100:
    raise RuntimeError("Failed preserve original straps: "+str(counts))
REPORT["base_face_counts"]=counts
REPORT["construction"]="Meshy source retained as timber core; newly manufactured forged-iron shell, separate oak ring and iron pegs"
REPORT["construction_approved"]=False

# The new hoop is made from the REAL existing Genesis oak PBR color / normal /
# roughness maps. The original mesh UV atlas wasn't meant for the new ring.
# For a transverse/radial hoop, unwrap grain along the circumference.
# The original source is the verified caprino V020 approved GLB.
# These are its PBR textures extracted, not generic brown colors.
def leather_material(name,finish):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bsdf=nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value=0
    uv=nodes.new("ShaderNodeTexCoord")
    mapping=nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value=(1,1,1)
    links.new(uv.outputs["UV"],mapping.inputs["Vector"])
    def tex(filename,space):
        n=nodes.new("ShaderNodeTexImage")
        n.image=bpy.data.images.load(str(LEATHER/filename),check_existing=True)
        n.image.colorspace_settings.name=space
        links.new(mapping.outputs["Vector"],n.inputs["Vector"])
        return n
    albedo=tex("leather_albedo_v020.png","sRGB")
    rough=tex("leather_roughness_v020.png","Non-Color")
    normal=tex("leather_normal_v020.png","Non-Color")
    node=nodes.new("ShaderNodeNormalMap")
    node.inputs["Strength"].default_value=1
    links.new(normal.outputs["Color"],node.inputs["Color"])
    links.new(node.outputs["Normal"],bsdf.inputs["Normal"])
    if finish=="v020_original":
        links.new(albedo.outputs["Color"],bsdf.inputs["Base Color"])
        links.new(rough.outputs["Color"],bsdf.inputs["Roughness"])
    elif finish=="experiment_oiled":
        # Same approved photo PBR maps; only its shield treatment is modified.
        tone=nodes.new("ShaderNodeMixRGB")
        tone.blend_type="MULTIPLY"
        tone.inputs[0].default_value=1.0
        tone.inputs[2].default_value=(.85,.79,.73,1)
        links.new(albedo.outputs["Color"],tone.inputs[1])
        links.new(tone.outputs["Color"],bsdf.inputs["Base Color"])
        mul=nodes.new("ShaderNodeMath")
        mul.operation="MULTIPLY"
        mul.inputs[1].default_value=.82
        links.new(rough.outputs["Color"],mul.inputs[0])
        links.new(mul.outputs[0],bsdf.inputs["Roughness"])
    else:raise RuntimeError("Invalid leather treatment")
    return mat
leather_a=leather_material("V015_A_Caprino_V020_APPROVED_SOURCE", "v020_original")
leather_b=leather_material("V015_B_Caprino_V020_oiled_UNAPPROVED", "experiment_oiled")
REPORT["leather_variants"]={
    "A":{"PBR_source":"approved caprino V020","roughness_factor":1,"approved_on_shield":False},
    "B":{"PBR_source":"approved caprino V020","roughness_factor":.82,"darker_tint":True,"approved_on_shield":False}}
# Helper: real mesh with intentional, auditable physical UV coordinates.
def mesh_with_uv(name,verts,faces,uvfaces,material,smooth=True):
    me=bpy.data.meshes.new(name+"_mesh")
    me.from_pydata(verts,[],faces);me.update()
    obj=bpy.data.objects.new(name,me)
    bpy.context.collection.objects.link(obj)
    me.materials.append(material)
    layer=me.uv_layers.new(name="UVMap")
    if len(uvfaces)!=len(me.polygons):
        raise RuntimeError("Missing UV face for "+name)
    for poly,face_uv in zip(me.polygons,uvfaces):
        if len(poly.loop_indices)!=len(face_uv):
            raise RuntimeError("UV vertex count mismatch "+name)
        for li,uvpair in zip(poly.loop_indices,face_uv):
            layer.data[li].uv=uvpair
        poly.use_smooth=smooth
    return obj

SEG=120
# A slight handmade wobble rather than a perfect, decorative torus.
def wiggle(a):return .0025*R*math.sin(9*a+0.37)+.0018*R*math.sin(17*a+1.2)
ring_verts=[]
ring_uvs=[]
front_y=ymn-.052*R
back_y=ymn+.16*R
# Four ring layers: inner front, outer front, outer back, inner back.
for layer_id in range(4):
    inner=layer_id in (0,3)
    rad=.825*R if inner else .997*R
    y0=front_y if layer_id<2 else back_y
    for i in range(SEG+1):
        a=2*math.pi*i/SEG
        rr=rad+wiggle(a)
        y=y0+.003*R*math.sin(7*a+0.91)
        ring_verts.append((c.x+rr*math.cos(a),y,c.z+rr*math.sin(a)))
        ring_uvs.append((i/SEG*4.5, (0,.30,.65,1)[layer_id]))
ring_faces=[]
ring_uvfaces=[]
for layer_a,layer_b in ((0,1),(1,2),(2,3),(3,0)):
    for i in range(SEG):
        v=[layer_a*(SEG+1)+i,layer_b*(SEG+1)+i,layer_b*(SEG+1)+i+1,layer_a*(SEG+1)+i+1]
        ring_faces.append(tuple(v))
        ring_uvfaces.append([ring_uvs[n] for n in v])
wood_hoop=mesh_with_uv("V015_Leather_Wrapped_Hoop_V020_PBR",ring_verts,ring_faces,ring_uvfaces,leather_a,True)

# Thin, slightly domed wrought-iron facing, made as its OWN metal object.
# Its outer edge is hidden beneath the oak hoop. It is not "wood dyed grey".
plate_verts=[]
plate_uvs=[]
RINGS=48  # actual surface vertices, not an illustrative texture
PLATE_R=.851*R
rng=random.Random(140514)
strikes=[]
for i in range(43):
    a=rng.uniform(0,2*math.pi)
    r=PLATE_R*math.sqrt(rng.uniform(.017,.78))
    # Many uneven broad beginner-blacksmith hammer impressions, with some
    # shallow ones facing outward for less mathematically perfect sheet.
    strikes.append({
        "x":r*math.cos(a),
        "z":r*math.sin(a),
        "major":R*rng.uniform(.075,.17),
        "minor":R*rng.uniform(.055,.14),
        "angle":rng.uniform(0,math.pi),
        "depth":R*rng.uniform(.0045,.0105)*(1 if i%7 else -.4)
    })
def hammer_geometry(x,z,rad):
    deformation=0.0
    for hit in strikes:
        dx=x-hit["x"];dz=z-hit["z"]
        cs=math.cos(hit["angle"]);sn=math.sin(hit["angle"])
        u=(cs*dx+sn*dz)/hit["major"]
        v=(-sn*dx+cs*dz)/hit["minor"]
        rr=u*u+v*v
        if rr<10:
            # Planar but softly rounded depression; varied anisotropy.
            deformation+=hit["depth"]*math.exp(-1.25*rr)
    # No changes at the plate edge; preserve leather/iron joint.
    fade=max(0,1-(rad/PLATE_R)**6)**3
    deformation=max(-.011*R,min(.022*R,deformation))*fade
    return deformation

# V015 — two hard and one secondary apprentice hammer blows near the steel edge.
# The source GLB, leather hoop and iron/leather junction must remain unchanged.
# Axes are the same x/z as the original iron plate; +Y is inward on the face.
edge_hits=[
    {"name":"left_upper_hard","angle_deg":159,"r_fraction":.82,"major_R":.185,"minor_R":.125,"depth_R":.034,"rotation_deg":23},
    {"name":"right_lower_hard","angle_deg":292,"r_fraction":.78,"major_R":.164,"minor_R":.108,"depth_R":.030,"rotation_deg":-33},
    {"name":"right_upper_medium","angle_deg":23,"r_fraction":.865,"major_R":.129,"minor_R":.090,"depth_R":.019,"rotation_deg":61},
]
for hit in edge_hits:
    ang=math.radians(hit["angle_deg"])
    hit["x"]=PLATE_R*hit["r_fraction"]*math.cos(ang)
    hit["z"]=PLATE_R*hit["r_fraction"]*math.sin(ang)
    assert .76<=hit["r_fraction"]<=.89
    assert hit["depth_R"]<.04
def strong_edge_deformation(x,z,rad):
    depression=0.0
    for hit in edge_hits:
        dx=x-hit["x"];dz=z-hit["z"]
        a=math.radians(hit["rotation_deg"]);cs=math.cos(a);sn=math.sin(a)
        u=(cs*dx+sn*dz)/(R*hit["major_R"])
        v=(-sn*dx+cs*dz)/(R*hit["minor_R"])
        rr=u*u+v*v
        if rr<12:
            # A shallow proud lip surrounding a broad, unequal, actual dent:
            # non-periodic relief rather than repeated microtexture rings.
            core=math.exp(-1.7*rr)
            raised_lip=.115*math.exp(-4*(math.sqrt(rr)-1.18)**2)
            depression+=R*hit["depth_R"]*(core-raised_lip)
    # Strongly protect the seam with the goatskin-bound perimeter.
    # At r/plate > .87 the force decays, becoming EXACTLY zero at the edge.
    t=max(0.0,min(1.0,(1.0-rad/PLATE_R)/.13))
    edge_protection=t*t*(3.0-2.0*t)
    return max(-.006*R,min(.042*R,depression))*edge_protection

plate_verts.append((c.x,ymn-.062*R+hammer_geometry(0,0,0),c.z))
plate_uvs.append((.5,.5))
for j in range(1,RINGS+1):
    rad=PLATE_R*j/RINGS
    for i in range(SEG):
        a=2*math.pi*i/SEG
        x=rad*math.cos(a)
        z=rad*math.sin(a)
        phase=math.sin(4*a+1.1)*math.sin(7*rad/R+0.4)
        hammer=(rad/PLATE_R)**2*(.0015*R*phase+.0007*R*math.sin(15*a+3.5*rad/R))
        y=ymn-.020*R-.042*R*(1-(rad/PLATE_R)**2)+hammer+hammer_geometry(x,z,rad)+strong_edge_deformation(x,z,rad)
        plate_verts.append((c.x+x,y,c.z+z))
        plate_uvs.append((.5+x/(2*PLATE_R),.5+z/(2*PLATE_R)))
plate_faces=[]
plate_uvfaces=[]
def plateidx(j,i):return 1+(j-1)*SEG+(i%SEG)
for i in range(SEG):
    v=(0,plateidx(1,i),plateidx(1,i+1))
    plate_faces.append(v);plate_uvfaces.append([plate_uvs[n] for n in v])
for j in range(1,RINGS):
    for i in range(SEG):
        v=(plateidx(j,i),plateidx(j+1,i),plateidx(j+1,i+1),plateidx(j,i+1))
        plate_faces.append(v)
        plate_uvfaces.append([plate_uvs[n] for n in v])
steel_plate=mesh_with_uv("V015_Solid_Forged_Iron_Sheet_V175",plate_verts,plate_faces,plate_uvfaces,iron,True)
steel_plate["source"]="V175 V153_FrontOxidation_Only_MatchedBack"
# Add irregular physical microsurface to the facing ONLY; the original V175
# shader stays intact underneath, and the rim/rivets/back keep their materials.
hammered_iron=iron.copy()
hammered_iron.name="V015_IronV175_Hammered_Only_Front_DERIVED"
steel_plate.data.materials[0]=hammered_iron
nodes=hammered_iron.node_tree.nodes
links=hammered_iron.node_tree.links
pbr=next((n for n in nodes if n.type=="BSDF_PRINCIPLED"),None)
if pbr is None:raise RuntimeError("V175 PBR principal unavailable in derived material")
coords=nodes.new("ShaderNodeTexCoord")
coords.label="V015 iron-only normalized planar microgeometry"
# Broad, irregular hammer micro-pits using smoothly rounded Voronoi cells.
vor=nodes.new("ShaderNodeTexVoronoi")
vor.feature="F1"
vor.distance="EUCLIDEAN"
vor.inputs["Scale"].default_value=43.0
vor.inputs["Randomness"].default_value=.93
links.new(coords.outputs["Generated"],vor.inputs["Vector"])
pit_ramp=nodes.new("ShaderNodeValToRGB")
pit_ramp.color_ramp.interpolation="EASE"
pit_ramp.color_ramp.elements[0].position=.12
pit_ramp.color_ramp.elements[0].color=(.16,.16,.16,1)
pit_ramp.color_ramp.elements[1].position=.51
pit_ramp.color_ramp.elements[1].color=(.86,.86,.86,1)
links.new(vor.outputs["Distance"],pit_ramp.inputs["Fac"])
pit=nodes.new("ShaderNodeBump")
pit.inputs["Strength"].default_value=.075
pit.inputs["Distance"].default_value=.0019*R
links.new(pit_ramp.outputs["Color"],pit.inputs["Height"])
# Fine non-periodic hammer/sanding grain.
micro=nodes.new("ShaderNodeTexNoise")
micro.inputs["Scale"].default_value=105
micro.inputs["Detail"].default_value=3.5
micro.inputs["Roughness"].default_value=.72
links.new(coords.outputs["Generated"],micro.inputs["Vector"])
fine=nodes.new("ShaderNodeBump")
fine.inputs["Strength"].default_value=.045
fine.inputs["Distance"].default_value=.00045*R
links.new(micro.outputs["Fac"],fine.inputs["Height"])
normal_source=next(iter(pbr.inputs["Normal"].links),None)
if normal_source:
    links.new(normal_source.from_socket,pit.inputs["Normal"])
links.new(pit.outputs["Normal"],fine.inputs["Normal"])
links.new(fine.outputs["Normal"],pbr.inputs["Normal"])
# Preserve the inherited original V175 roughness network and multiply by a
# slow noise field instead of substituting an arbitrary grey surface.
rough_source=next(iter(pbr.inputs["Roughness"].links),None)
original_roughness=pbr.inputs["Roughness"].default_value
rough_noise=nodes.new("ShaderNodeTexNoise")
rough_noise.inputs["Scale"].default_value=18.5
rough_noise.inputs["Detail"].default_value=4.0
rough_noise.inputs["Roughness"].default_value=.72
links.new(coords.outputs["Generated"],rough_noise.inputs["Vector"])
rough_map=nodes.new("ShaderNodeMapRange")
rough_map.inputs["From Min"].default_value=.20
rough_map.inputs["From Max"].default_value=.80
rough_map.inputs["To Min"].default_value=.91
rough_map.inputs["To Max"].default_value=1.10
rough_map.clamp=True
links.new(rough_noise.outputs["Fac"],rough_map.inputs["Value"])
rough_mul=nodes.new("ShaderNodeMath")
rough_mul.operation="MULTIPLY"
if rough_source:
    links.new(rough_source.from_socket,rough_mul.inputs[0])
else:
    rough_mul.inputs[0].default_value=original_roughness
links.new(rough_map.outputs["Result"],rough_mul.inputs[1])
clamp=nodes.new("ShaderNodeClamp")
clamp.inputs["Min"].default_value=.18
clamp.inputs["Max"].default_value=.97
links.new(rough_mul.outputs["Value"],clamp.inputs["Value"])
links.new(clamp.outputs["Result"],pbr.inputs["Roughness"])
REPORT["hammered_iron"]={
    "base_iron_shader":"V153_FrontOxidation_Only_MatchedBack from exact V175 workcopy",
    "surface_only":"V015_Solid_Forged_Iron_Sheet_V175",
    "deterministic_seed":140514,
    "macro_strikes_count":len(strikes),
    "real_mesh_plate_rings":RINGS,
    "real_mesh_circumferential_segments":SEG,
    "dent_depth_range_relative_to_R":[-.011,.022],"strong_edge_depth_max_relative_to_R":.034,"strong_edge_hits":[{k:hit[k] for k in ("name","angle_deg","r_fraction","major_R","minor_R","depth_R","rotation_deg")} for hit in edge_hits],
    "macro_geometry_untouched_at_edge":True,
    "microbump_strength":.075,
    "microbump_distance_relative_to_R":.0019,
    "finegrain_strength":.045,
    "finegrain_distance_relative_to_R":.00045,
    "roughness_multiplier_range":[.91,1.10],
    "metallic_unmodified":True,
    "leather_oak_wood_pegs_materials_unmodified":True,
    "base_original_Meshy_GLBSHA_verified":True,
    "asset_approval":"pending visual review"
}

steel_plate["steel_sheet_thickness_m"]=.004
# Solidify adds genuine metal thickness without damaging the reference mesh.
solid=steel_plate.modifiers.new("Wrought iron sheet thickness","SOLIDIFY")
solid.thickness=.004*R
solid.offset=1
rim_bevel=steel_plate.modifiers.new("Handworked edge rounding","BEVEL")
rim_bevel.width=.0017*R
rim_bevel.segments=2

# Eight crude wooden-rim fasteners + four inner plate pegs.
# Simple handmade iron domes, not decorative studs.
pegs=[]
for i in range(8):
    ang=2*math.pi*i/8+math.pi/2
    radius=.91*R
    x=c.x+radius*math.cos(ang)
    z=c.z+radius*math.sin(ang)
    y=front_y-.006*R
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=7,radius=.026*R,location=(x,y,z))
    bolt=bpy.context.object
    bolt.name="V015_Hoop_Iron_Peg_%02d"%(i+1)
    bolt.scale.y=.38
    bolt.data.materials.append(iron)
    pegs.append(bolt)
for i in range(4):
    ang=2*math.pi*i/4+math.pi/4
    radius=.72*R
    x=c.x+radius*math.cos(ang)
    z=c.z+radius*math.sin(ang)
    y=ymn-.020*R-.042*R*(1-(radius/PLATE_R)**2)-.008*R
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=7,radius=.018*R,location=(x,y,z))
    bolt=bpy.context.object
    bolt.name="V015_Facing_Iron_Peg_%02d"%(i+1)
    bolt.scale.y=.45
    bolt.data.materials.append(iron)
    pegs.append(bolt)
# Audit actual source and derived meshes separately, retain approval gate.
REPORT["front_geometry_revision"]="Remove duplicated angle seam; hammer distortion fades to zero at center; pole height follows plate parabola"
REPORT["material_change_only"]="V009 geometry untouched; real oak hoop material replaced with leather V020 in A/B"
REPORT["new_geometry"]={
    "steel_plate_faces":len(steel_plate.data.polygons),
    "leather_hoop_faces":len(wood_hoop.data.polygons),
    "steel_peg_objects":len(pegs),
    "source_triangles":REPORT["source_triangles"],
    "front_plate_radius":PLATE_R,"wood_hoop_outer_radius":.997*R,
    "source_mesh_preserved":True,
    "source_mesh_original_mat":original_mat.name,
    "oak_material":oak.name,
    "leather_a_material":leather_a.name,"leather_b_material":leather_b.name,
    "iron_material":iron.name}

# Exact approved V020 caprine lighting profile reference:
# ProjectgenesisAssets/genesis-workshop-assets
# evaluation/tanned-goatskin/V020_OWNER_APPROVED.json
# 4600K key, studio_small_09_2k.hdr 32-bit RGBE, strength 0.82,
# area lamp center (3,-4,5), power 12, size 4. No stronger auxiliary lights.
world=bpy.data.worlds.new("Genesis_APPROVED_CAPRINO_V020_HDRI_09_RGBE32")
world.use_nodes=True
nodes=world.node_tree.nodes;nodes.clear()
environment=nodes.new("ShaderNodeTexEnvironment")
environment.image=bpy.data.images.load(str(HDRI),check_existing=True)
if environment.image.file_format!="HDR":
    raise RuntimeError("Approved caprino HDRI must be real 32-bit HDR")
bg=nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value=0.82
output=nodes.new("ShaderNodeOutputWorld")
world.node_tree.links.new(environment.outputs["Color"],bg.inputs["Color"])
world.node_tree.links.new(bg.outputs["Background"],output.inputs["Surface"])
scene=bpy.context.scene
scene.world=world
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=64
scene.cycles.use_denoising=False
scene.render.resolution_x=1100
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.view_settings.view_transform="Standard"
scene.view_settings.exposure=0
light=bpy.data.lights.new("Genesis Approved V020 4600K Area Key",type="AREA")
obj=bpy.data.objects.new("Genesis Approved V020 4600K Area Key",light)
scene.collection.objects.link(obj)
obj.location=(3,-4,5)
light.shape="DISK"
light.size=4
light.energy=12
light.use_nodes=True
lightnodes=light.node_tree.nodes
lightlinks=light.node_tree.links
emission=next((n for n in lightnodes if n.type=="EMISSION"),None)
if emission is None: emission=lightnodes.new("ShaderNodeEmission")
light_output=next((n for n in lightnodes if n.type=="OUTPUT_LIGHT"),None)
if light_output is None: light_output=lightnodes.new("ShaderNodeOutputLight")
lightlinks.new(emission.outputs["Emission"],light_output.inputs["Surface"])
emission.inputs["Strength"].default_value=12.0
blackbody=lightnodes.new("ShaderNodeBlackbody")
blackbody.inputs["Temperature"].default_value=4600.0
lightlinks.new(blackbody.outputs["Color"],emission.inputs["Color"])
obj.rotation_euler=(c-obj.location).to_track_quat("-Z","Y").to_euler()
REPORT["lighting_profile"]={
   "name":"Approved V020 caprine inventory lighting profile, applied to shield",
   "source_repo":"ProjectgenesisAssets/genesis-workshop-assets",
   "source_file":"evaluation/tanned-goatskin/V020_OWNER_APPROVED.json",
   "temperature_kelvin":4600,
   "reference_hdri":"studio_small_09_2k.hdr",
   "world_strength":0.82,
   "area_key_energy":12,
   "area_key_emission_strength":12,
   "area_key_size":4,
   "area_key_location":[3,-4,5],
   "view_transform":"Standard",
   "exposure":0,
   "extra_softboxes":0,
   "asset_geometry_and_pbr_unchanged":True,
   "lighting_approved_as_caprine_inventory_reference_not_shield_final":True}
# V015 keeps the owner-approved V020 caprine 4600K + HDRI studio_small_09
# profile identical. The dedicated light is linked ONLY to iron geometry,
# leaving the leather and wood untouched. Test two iron-only intensities.
receivers=bpy.data.collections.new("V015_Only_Iron_Front_Light_Receivers")
scene.collection.children.link(receivers)
receivers.objects.link(steel_plate)
for iron_peg in pegs:receivers.objects.link(iron_peg)
iron_sweep_data=bpy.data.lights.new("V015_Iron_Only_Soft_Specular",type="AREA")
iron_sweep_obj=bpy.data.objects.new("V015_Iron_Only_Soft_Specular",iron_sweep_data)
scene.collection.objects.link(iron_sweep_obj)
iron_sweep_obj.location=c+Vector((-0.9,-2.45,1.3))*R
iron_sweep_obj.rotation_euler=(c-iron_sweep_obj.location).to_track_quat("-Z","Y").to_euler()
iron_sweep_data.shape="DISK"
iron_sweep_data.size=1.7*R
iron_sweep_obj.light_linking.receiver_collection=receivers
assert iron_sweep_obj.light_linking.receiver_collection==receivers
assert steel_plate.name in receivers.objects
assert wood_hoop.name not in receivers.objects
assert ob.name not in receivers.objects
REPORT["light_link_test"]={
  "source":"Cycles Blender 4.5.13 LTS light linking receiver collection",
  "base_profile_kelvin":4600,
  "hdri_base_unchanged":"studio_small_09_2k.hdr / 0.82",
  "linked_objects":[o.name for o in receivers.objects],
  "leather_affected_by_new_light":False,
  "oak_rear_affected_by_new_light":False,
  "base_materials_and_geometry_unchanged":True,
  "sweep_light_shape":"DISK",
  "sweep_light_size_relative_to_R":1.7,
  "sweep_light_offset_relative_to_R":[-0.9,-2.45,1.3],
  "test_powers_watts":[110,260],
  "not_a_game_lighting_setting":True,
  "approval_state":"experimental_only"
}

camdat=bpy.data.cameras.new("Escudo_V015_Camera")
cam=bpy.data.objects.new("Escudo_V005_Camera",camdat)
scene.collection.objects.link(cam)
camdat.type="ORTHO";scene.camera=cam
def render(name,side,angle=False,detail=False):
    direction=Vector((0,float(side)*3.5,0))
    if angle:direction+=Vector((1.3,0,0.75))
    cam.location=c+direction*R
    cam.rotation_euler=(c-cam.location).to_track_quat("-Z","Y").to_euler()
    camdat.ortho_scale=max(dm[0],dm[2])*(.94 if detail else (1.4 if angle else 1.33))
    p=OUT/(name+".png")
    scene.render.filepath=str(p)
    bpy.ops.render.render(write_still=True)
    if not p.is_file() or p.stat().st_size<1000:raise RuntimeError("Missing actual render "+name)
    REPORT["renders"].append({"file":p.name,"bytes":p.stat().st_size,"sha256":sha(p)})
# V015: use preferred V010A leather unchanged. Correct lighting only.
wood_hoop.data.materials[0]=leather_a
REPORT["lighting_comparison"]={"reference":"V013B","iron_only_softbox_watts":260,"4600k_profile_unchanged":True,"leather_and_wood_unchanged":True,"V014_43_macro_hits_preserved":True,"V015_3_edge_hits_added":True,"fine_bump_reduced":True}
# Only 3 fresh visual tests: front, 3/4, and tight detail. Back unchanged.
wood_hoop.data.materials[0]=leather_a
iron_sweep_data.energy=260
render("V015_01_frente_golpes_fuertes",-1)
render("V015_02_tres_cuartos",-1,True)
render("V015_03_detalle_golpes_borde",-1,detail=True)
scene.render.filepath=""
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"escudo_v015_revision.blend"))
REPORT["status"]="rendered_pending_human_review"
(OUT/"report_v015.json").write_text(json.dumps(REPORT,indent=2,ensure_ascii=False),encoding="utf-8")
print("GENESIS_SHIELD_V015_OK",json.dumps({"renders":REPORT["renders"],"construction":REPORT["new_geometry"]}))
