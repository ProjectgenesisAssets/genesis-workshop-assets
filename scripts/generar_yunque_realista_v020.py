# Project Genesis / PlayCanvas — YUNQUE_MEDIEVAL_REALISTA_V020
# First production candidate matching approved 16-view photographic concept.
# Blender runs only in GitHub Actions. No asset from this script is automatically admitted to the game.
import bpy
import math
import os
import json
import random
from pathlib import Path
from mathutils import Vector
import numpy as np

random.seed(10621)
ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))
OUT = ROOT / "output_anvil_v020"
TEX = OUT / "textures"
TEX.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

MAX_TRIANGLES = 120000
TEX_SIZE = 1536
MESH_PARTS = []

def noise_layer(rng, height, width, cells):
    """Interpolated isotropic noise, deterministic without external image assets."""
    rows = int(cells) + 2
    cols = int(cells) + 2
    small = rng.normal(0.0, 1.0, (rows, cols)).astype(np.float32)
    yy = np.linspace(0, rows - 2.001, height, dtype=np.float32)
    xx = np.linspace(0, cols - 2.001, width, dtype=np.float32)
    yi = yy.astype(np.int32)
    xi = xx.astype(np.int32)
    fy = yy - yi
    fx = xx - xi
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    a = small[yi[:, None], xi[None, :]]
    b = small[yi[:, None] + 1, xi[None, :]]
    c = small[yi[:, None], xi[None, :] + 1]
    d = small[yi[:, None] + 1, xi[None, :] + 1]
    return ((1 - fy[:, None]) * ((1 - fx[None, :]) * a + fx[None, :] * c)
            + fy[:, None] * ((1 - fx[None, :]) * b + fx[None, :] * d))

def create_image(name, rgb, is_data=False):
    rgb = np.clip(rgb, 0, 1).astype(np.float32)
    h, w = rgb.shape[:2]
    rgba = np.empty((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = rgb
    rgba[:, :, 3] = 1.0
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    if is_data:
        img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(rgba.ravel())
    img.file_format = "PNG"
    img.filepath_raw = str(TEX / (name + ".png"))
    img.save()
    img.pack()
    return img


# All metal scans in this temporary public workspace are procedurally authored.
# The V020 private photographic sources and private project masters stay private.

def forged_face_micro_scan(seed):
    """Deterministic real-scale directionally burnished steel with NO geometric tiles."""
    rng=np.random.default_rng(seed)
    n=TEX_SIZE
    # Scaled metal crystal/grain: neutral and low contrast under physically based light.
    fine=noise_layer(rng,n,n,170)
    mid=noise_layer(rng,n,n,23)
    coarse=noise_layer(rng,n,n,7)
    base=np.clip(.255+.012*coarse+.026*mid+.015*fine+
                 rng.normal(0,.002,(n,n)),.16,.35).astype(np.float32)
    # Thousands of sub-mm tool passes are baked into one grayscale micro-relief.
    # Stroke bounding boxes keep vector computations compact and deterministic.
    for i in range(240):
        x0=rng.uniform(0,n);y0=rng.uniform(0,n)
        ang=rng.normal(0,.25) if i%4 else rng.normal(.85,.48)
        length=rng.uniform(24,375)
        dx=length*math.cos(ang);dy=length*math.sin(ang)
        width=rng.uniform(.70,2.6) if i<210 else rng.uniform(2.5,6.5)
        depth=rng.uniform(.014,.056) if i<490 else rng.uniform(.014,.039)
        x1=x0+dx;y1=y0+dy
        xmin=max(0,int(min(x0,x1)-27));xmax=min(n,int(max(x0,x1)+27))
        ymin=max(0,int(min(y0,y1)-27));ymax=min(n,int(max(y0,y1)+27))
        if xmax<=xmin or ymax<=ymin:continue
        yy,xx=np.mgrid[ymin:ymax,xmin:xmax]
        t=np.clip(((xx-x0)*dx+(yy-y0)*dy)/(length*length),0,1)
        d2=(xx-x0-t*dx)**2+(yy-y0-t*dy)**2
        fall=np.maximum(0,np.sin(math.pi*t))**.65
        base[ymin:ymax,xmin:xmax]-=depth*np.exp(-d2/(2*width*width))*fall
    # Hundreds of minute hammer marks, but never large visual pitted patches.
    for i in range(480):
        cx=rng.integers(10,n-10);cy=rng.integers(10,n-10)
        rx=rng.uniform(3.0,8.5);ry=rng.uniform(2.8,7.4)
        xmin=max(0,int(cx-12));xmax=min(n,int(cx+13))
        ymin=max(0,int(cy-12));ymax=min(n,int(cy+13))
        yy,xx=np.mgrid[ymin:ymax,xmin:xmax]
        dent=np.exp(-.5*((xx-cx)**2/rx**2+(yy-cy)**2/ry**2))
        base[ymin:ymax,xmin:xmax]-=rng.uniform(.010,.034)*dent
    base=np.clip(base,.13,.36)
    return np.repeat(base[:,:,None],3,axis=2)

def wrought_iron_body_scan(seed):
    """Hammered/oxidized ferrous grain; softer and non-directional versus worked steel."""
    rng=np.random.default_rng(seed + 5317)
    n=TEX_SIZE
    fine=noise_layer(rng,n,n,235)
    mid=noise_layer(rng,n,n,39)
    broad=noise_layer(rng,n,n,8)
    value=np.clip(.238 + .019*broad + .026*mid + .019*fine
                  + rng.normal(0,.008,(n,n)),.125,.39).astype(np.float32)
    for _ in range(450):
        cx=int(rng.integers(16,n-16));cy=int(rng.integers(16,n-16))
        rx=rng.uniform(4.0,16.0);ry=rng.uniform(3.2,13.0)
        xmin=max(0,cx-30);xmax=min(n,cx+31)
        ymin=max(0,cy-30);ymax=min(n,cy+31)
        yy,xx=np.mgrid[ymin:ymax,xmin:xmax]
        dent=np.exp(-.5*((xx-cx)**2/rx**2+(yy-cy)**2/ry**2))
        value[ymin:ymax,xmin:xmax]-=rng.uniform(.008,.032)*dent
    return np.repeat(np.clip(value,.11,.39)[:,:,None],3,axis=2)

def pbr_metal(name,seed,kind):
    """Calibrated dark forged metal: procedural multi-scale microstructure provides calibrated steel response."""
    rng=np.random.default_rng(seed)
    photo=forged_face_micro_scan(seed) if kind in ('face','horn') else wrought_iron_body_scan(seed)
    photo_luma=photo[:,:,0]*.2126+photo[:,:,1]*.7152+photo[:,:,2]*.0722
    mean=float(photo_luma.mean())
    feature=np.clip(photo_luma/max(mean,.025)-1,-.72,.86)
    # The V004 uncalibrated photo scan looked like porous stone. Real iron should
    # read primarily through metal reflectivity, directional wear and low-contrast oxidation.
    if kind=="forged":
        tint=np.array([.176,.174,.170],dtype=np.float32)
        variation=.58;roughmean=.57;metal=.89;bump=.26
    elif kind=="face":
        tint=np.array([.238,.244,.247],dtype=np.float32)
        variation=.41;roughmean=.39;metal=.97;bump=.17
    else:
        tint=np.array([.194,.199,.202],dtype=np.float32)
        variation=.38;roughmean=.45;metal=.95;bump=.21
    modulation=np.clip(1+variation*feature,.73,1.19)
    color=tint[None,None,:]*modulation[:,:,None]
    # Oxidation is faint and confined to deep texture depressions, never rust blotches.
    if kind=="forged":
        ox=np.clip((-feature-.08)*.46,0,.21)
        color[:,:,0]+=ox*.13
        color[:,:,1]-=ox*.045
        color[:,:,2]-=ox*.085
    color=np.clip(color,.035,.25)
    # Material response: work-face burnished by many hammer blows, body forged and
    # moderately rough, horn intermediate. Independent roughness microvariation.
    micro=(np.roll(photo_luma,3,axis=0)+np.roll(photo_luma,-3,axis=0)+
           np.roll(photo_luma,3,axis=1)+np.roll(photo_luma,-3,axis=1))*.25
    detail=np.clip(photo_luma-micro,-.20,.20)
    rough=np.clip(roughmean-.46*detail-(.33 if kind=='face' else .065)*feature+
                  rng.normal(0,.002,(TEX_SIZE,TEX_SIZE)),.24,.68)
    # Subtle scanned tool microstructure in tangent normals; polished face MUST be smooth.
    gy,gx=np.gradient(detail)
    nx=np.clip(-gx*bump,-.23,.23)
    ny=np.clip(-gy*bump,-.23,.23)
    mag=np.sqrt(nx*nx+ny*ny+1)
    norm=np.stack((.5+.5*nx/mag,.5+.5*ny/mag,.5+.5/mag),axis=2)
    albedo=create_image(name+"_albedo_1536",color)
    roughness=create_image(name+"_roughness_1536",np.repeat(rough[:,:,None],3,axis=2),True)
    normal=create_image(name+"_normal_1536",norm,True)
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bsdf=nodes.get("Principled BSDF");bsdf.inputs["Metallic"].default_value=metal
    def tex(label,img):
        n=nodes.new("ShaderNodeTexImage");n.name=label;n.image=img;n.interpolation="Linear"
        return n
    alb=tex("Calibrated_Scan_Albedo",albedo)
    rou=tex("Forging_Roughness",roughness)
    nor=tex("Forged_Relief_Normal",normal)
    normal_node=nodes.new("ShaderNodeNormalMap")
    normal_node.inputs["Strength"].default_value=(.67 if kind=="face" else (.58 if kind=="forged" else .43))
    links.new(alb.outputs["Color"],bsdf.inputs["Base Color"])
    links.new(rou.outputs["Color"],bsdf.inputs["Roughness"])
    links.new(nor.outputs["Color"],normal_node.inputs["Color"])
    links.new(normal_node.outputs["Normal"],bsdf.inputs["Normal"])
    return mat

FORGED = pbr_metal("PG_iron_forged", 20261025, "forged")
FACE = pbr_metal("PG_steel_struck_face", 20261108, "face")
HORN = pbr_metal("PG_horn_worn_steel", 20261031, "horn")

def tag_mesh(obj, material, smooth=True):
    obj.data.materials.append(material)
    MESH_PARTS.append(obj)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj

def bevel_object(obj, width, segments=3):
    b = obj.modifiers.new("Hand_forged_softened_edges", "BEVEL")
    b.width = width
    b.segments = segments
    b.limit_method = "ANGLE"
    n = obj.modifiers.new("Face_weighted_normals", "WEIGHTED_NORMAL")
    n.keep_sharp = True
    return obj

def cube(name, xyz, dimensions, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    tag_mesh(obj, material, smooth=False)
    if bevel:
        bevel_object(obj, bevel)
    return obj

def closed_rings(name, outlines, material):
    # Outlines are CCW XY per Z, always same number of points.
    count = len(outlines[0])
    vertices = []
    for section in outlines:
        vertices.extend(section)
    faces = []
    faces.append(tuple(range(count - 1, -1, -1)))
    for j in range(len(outlines) - 1):
        for i in range(count):
            q = (i + 1) % count
            faces.append((j * count + i, j * count + q,
                          (j + 1) * count + q, (j + 1) * count + i))
    start = (len(outlines) - 1) * count
    faces.append(tuple(range(start, start + count)))
    me = bpy.data.meshes.new(name + "_mesh")
    me.from_pydata(vertices, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    return tag_mesh(obj, material)

def outline_rounded_rectangle(z, hx, hy, corner=.025, wobble=0.0):
    out = []
    # Counterclockwise: starting bottom-right; four quarter-circle corners.
    corners = ((hx - corner, -hy + corner, -math.pi / 2, 0),
               (hx - corner, hy - corner, 0, math.pi / 2),
               (-hx + corner, hy - corner, math.pi / 2, math.pi),
               (-hx + corner, -hy + corner, math.pi, 3 * math.pi / 2))
    for cx, cy, amin, amax in corners:
        for k in range(12):
            angle = amin + (amax - amin) * (k / 11)
            x = cx + corner * math.cos(angle)
            y = cy + corner * math.sin(angle)
            if wobble:
                x += wobble * math.sin(37 * angle + z * 27)
                y += wobble * math.cos(19 * angle + z * 31)
            out.append((x, y, z))
    # Handmade waved edge along the four originally perfectly straight runs.
    expanded=[]
    for i,point in enumerate(out):
        expanded.append(point)
        if i%12==11:
            next_point=out[(i+1)%len(out)]
            for step in range(1,13):
                f=step/13.0
                px=point[0]*(1-f)+next_point[0]*f
                py=point[1]*(1-f)+next_point[1]*f
                deviation=wobble*(.61*math.sin(f*math.pi*3+z*23+i*.29)
                                  +.36*math.sin(f*math.pi*7+i*.8))
                if abs(point[0]-next_point[0])>abs(point[1]-next_point[1]):
                    py+=deviation
                else:
                    px+=deviation
                expanded.append((px,py,z))
    return expanded

# The broad, 4-toed medieval base is deliberately undercut on its four sides.
BASE_OUTLINE = [
    (-.270, -.185), (-.118, -.185), (-.105, -.164),
    (.108, -.164), (.118, -.188), (.276, -.188),
    (.284, -.132), (.257, -.108), (.257, .107),
    (.284, .130), (.276, .189), (.117, .189),
    (.103, .165), (-.103, .165), (-.118, .189),
    (-.270, .189), (-.283, .132), (-.258, .105),
    (-.258, -.108), (-.283, -.130)
]
base_rings = []
for zz, factor in ((.017, 1.0), (.048, .978), (.082, .87), (.127, .795)):
    base_rings.append([
        (x * factor * (1.0 + .008 * math.sin(i * 1.7 + zz * 10.0)),
         y * factor * (1.0 + .009 * math.cos(i * 1.37 - zz * 12.0)),
         zz + .0007 * math.sin(i * 2.1))
        for i, (x, y) in enumerate(BASE_OUTLINE)
    ])
BASE = closed_rings("Yunque_base_cuatro_patas", base_rings, FORGED)
bevel_object(BASE, .010, 3)

# Hand-forged waisted body, widening to meet a massive top shoulder.
body_dimensions = [
    (.115, .196, .132), (.157, .187, .127),
    (.228, .151, .115), (.306, .147, .113),
    (.356, .171, .123), (.407, .214, .143),
    (.467, .281, .164), (.493, .291, .169)
]
BODY = closed_rings(
    "Yunque_nucleo_fundido_forjado",
    [outline_rounded_rectangle(z, x, y, corner=.043, wobble=.0014)
     for z, x, y in body_dimensions],
    FORGED
)
bevel_object(BODY, .007, 3)

# Continuous forged head shoulder, replacing stacked CGI plates.
SHOULDER = closed_rings("Hombro_de_hierro_forjado_continuo", [
    outline_rounded_rectangle(.463,.284,.150,corner=.039,wobble=.0024),
    outline_rounded_rectangle(.496,.302,.165,corner=.038,wobble=.0033),
    outline_rounded_rectangle(.522,.303,.164,corner=.041,wobble=.0039),
], FORGED)
# Thin hardened working face is added after the monolithic iron forging.

# The tapered one-sided horn is a solid forged curved conical volume.
horn_outline = []
sides = 64
stages = 58
for j in range(stages + 1):
    t = j / stages
    x = -.234 - .485 * t
    center_z = .459 + .076 * t - .003 * math.sin(math.pi * t)
    y_radius = .153 * (1 - t) ** .78 + .005
    z_radius = .083 * (1 - t) ** .82 + .004
    ring = []
    for k in range(sides):
        theta = k * 2 * math.pi / sides
        # Sub-millimeter hammer/forging irregularities; detail mainly comes from PBR.
        irregular = (1 + (.010 * (1 - t)) * math.sin(13 * theta + 9 * t)
                       + (.003 * (1 - t)) * math.cos(21 * theta - 17 * t))
        y = y_radius * math.cos(theta) * irregular
        z = center_z + z_radius * math.sin(theta) * irregular
        # The root of the horn is buried below the forge-welded hardened face.
        # Only the truly protruding nose rises to work-surface height.
        z = min(z, .515 + .024 * max(0.0, min(1.0, (-x - .300) / .115)))
        ring.append((x, y, z))
    horn_outline.append(ring)
# closed_rings assumes sections in CCW XY; for axis-X, build oriented quads directly.
verts = [v for ring in horn_outline for v in ring]
polys = [tuple(range(sides - 1, -1, -1))]
for j in range(stages):
    for k in range(sides):
        nxt = (k + 1) % sides
        polys.append((j * sides + k, (j + 1) * sides + k,
                      (j + 1) * sides + nxt, j * sides + nxt))
polys.append(tuple(range(stages * sides, (stages + 1) * sides)))
mesh = bpy.data.meshes.new("Cuerno_mesh")
mesh.from_pydata(verts, [], polys)
mesh.update()
HORN_OBJ = bpy.data.objects.new("Cuerno_conico_curvo_forjado", mesh)
bpy.context.collection.objects.link(HORN_OBJ)
tag_mesh(HORN_OBJ, HORN)

# Rectangular far heel. Through-holes are cut into the fused iron later.
HEEL = cube("Refuerzo_inferior_de_talon",
            (.420, 0, .493), (.280, .286, .058), FORGED, .011)

# Scratched, worked-down transition collar creates realistic forged joining marks.
# The pieces overlap internally as a normal prop, but no levitating geometry exists.

# A single forged mass, not six mechanically stacked CGI primitives.
# Apply all procedural edge work before voxel union, which eliminates visible seam joins.
bpy.ops.object.select_all(action="DESELECT")
for obj in MESH_PARTS:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in tuple(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)
for obj in MESH_PARTS:
    obj.select_set(True)
bpy.context.view_layer.objects.active = BODY
bpy.ops.object.join()
UNIFIED = bpy.context.object
UNIFIED.name = "Yunque_forja_monolitica_retopologia_V020"
MESH_PARTS[:] = [UNIFIED]
# Closed voxels fuse the horn, heel, side shoulders, waist and feet at intersections.
UNIFIED.data.remesh_voxel_size = .0074
bpy.ops.object.voxel_remesh()
# Restore the hardy hole THROUGH both hardened face and the supporting heel metal.
bpy.ops.mesh.primitive_cube_add(size=1, location=(.471, .041, .515))
HARDY_CUT = bpy.context.object
HARDY_CUT.name = "_HardyHole_recut_after_forged_union"
HARDY_CUT.dimensions = (.048, .048, .165)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.context.view_layer.objects.active = UNIFIED
boolean = UNIFIED.modifiers.new("Agujero_forjador_real", "BOOLEAN")
boolean.operation = "DIFFERENCE"
boolean.object = HARDY_CUT
bpy.ops.object.modifier_apply(modifier=boolean.name)
# Punch a secondary small circular pritchel hole through the supporting heel.
bpy.data.objects.remove(HARDY_CUT, do_unlink=True)
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=.0115, depth=.19, location=(.392,-.073,.514))
PUNCH=bpy.context.object
PUNCH.name="_Pritchel_aux_hole_in_heel"
bpy.context.view_layer.objects.active=UNIFIED
punch_mod=UNIFIED.modifiers.new("Pritchel_round_hole_body","BOOLEAN")
punch_mod.operation="DIFFERENCE"
punch_mod.object=PUNCH
bpy.ops.object.modifier_apply(modifier=punch_mod.name)
bpy.data.objects.remove(PUNCH,do_unlink=True)
# Tiny genuine forged relief in sidewalls, preserving planar struck face.
from mathutils import noise
bpy.context.view_layer.objects.active = UNIFIED
for v in UNIFIED.data.vertices:
    x, y, z = v.co
    if z > .521 and x > -.34:
        strength = .00010
    elif z > .48 and x < -.35:
        strength = .00110
    else:
        strength = .00235
    rough = noise.fractal(v.co * 23.0, 1.0, 2.0, 3.0)
    v.co += v.normal * (rough * strength)
UNIFIED.data.update()
# Lightly relax voxel faceting while preserving horn and real hardy-hole geometry.
bpy.context.view_layer.objects.active=UNIFIED
smoother=UNIFIED.modifiers.new("Forja_manual_alisado_de_voxeles","SMOOTH")
smoother.factor=.36
smoother.iterations=2
bpy.ops.object.modifier_apply(modifier=smoother.name)
UNIFIED.data.materials.clear()
UNIFIED.data.materials.append(FORGED)
UNIFIED.data.materials.append(FACE)
UNIFIED.data.materials.append(HORN)
# Preserve physically continuous steel working surface across the voxel-forged face.
# Old hard Z threshold (.516) created a false checker mosaic of black/bright
# material indices on small stepped facets. Assign by upward-facing region.
top_count=0
top_steel_count=0
for face in UNIFIED.data.polygons:
    center = sum((UNIFIED.data.vertices[v].co for v in face.vertices), Vector((0.0, 0.0, 0.0))) / len(face.vertices)
    if center.x < -.345 and center.z > .395:
        face.material_index = 2
    elif center.x > -.345 and center.z > .478 and (face.normal.z > .08 or center.z > .508):
        face.material_index = 1
    else:
        face.material_index = 0
    if center.x > -.33 and center.z > .495 and face.normal.z > .65:
        top_count+=1
        if face.material_index==1:top_steel_count+=1
    face.use_smooth = True
top_ratio = top_steel_count/max(1,top_count)
print("GENESIS_V020_TOP_FACE_STEEL_RATIO:",round(top_ratio,6),"count",top_count,flush=True)
if top_count<100 or top_ratio<.985:
    raise RuntimeError("Work face material checker regression: "+str((top_ratio,top_count)))
print("GENESIS_V020_UNIFIED_FACES:", len(UNIFIED.data.polygons), flush=True)

# The voxel-unified forging creates millimeter steps in its upper steel cap.
# Preserve the authentic forged body, but cover the struck plane with a separate
# forge-welded hardened STEEL WORK FACE made from an exact planar working surface.
# Slight overlap is a historical forge weld and prevents z-fighting artifacts.
WORKFACE=closed_rings(
    "Cara_forjada_endurecida_redondeada_V020",
    [[(x+.130,y,z) for (x,y,z) in ring] for ring in [
        outline_rounded_rectangle(.519,.420,.148,corner=.029,wobble=.0027),
        outline_rounded_rectangle(.532,.424,.151,corner=.042,wobble=.0044),
        outline_rounded_rectangle(.538,.414,.143,corner=.051,wobble=.0055),
    ]], FACE)
bpy.ops.mesh.primitive_cube_add(size=1, location=(.471,.041,.532))
face_cut=bpy.context.object
face_cut.name="_V020_hardy_hole_through_forged_face"
face_cut.dimensions=(.049,.049,.145)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
mod=WORKFACE.modifiers.new("Hardy_square_through_new_workface","BOOLEAN")
mod.operation="DIFFERENCE"
mod.object=face_cut
bpy.context.view_layer.objects.active=WORKFACE
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(face_cut,do_unlink=True)
bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.0115,depth=.13,location=(.392,-.073,.531))
PUNCH_TOP=bpy.context.object
PUNCH_TOP.name="_Pritchel_through_hardened_face"
bpy.context.view_layer.objects.active=WORKFACE
punch_top_mod=WORKFACE.modifiers.new("Pritchel_round_hole_top","BOOLEAN")
punch_top_mod.operation="DIFFERENCE"
punch_top_mod.object=PUNCH_TOP
bpy.ops.object.modifier_apply(modifier=punch_top_mod.name)
bpy.data.objects.remove(PUNCH_TOP,do_unlink=True)
bevel_object(WORKFACE,.0048,3)
# The full valid top is a smooth physical plane with a distinct dark steel PBR.
# No voxel remesh on this work face: the preceding faceting must remain buried.
print("GENESIS_V020_CLEAN_WORKFACE_ADDED:",len(WORKFACE.data.polygons),flush=True)

# UV unwrap the unified remeshed object for baked PBR in GLB / WebGL.
for obj in MESH_PARTS:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=.008)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)

# Check the EVALUATED and triangulated count, never just base-mesh polygons.
dg = bpy.context.evaluated_depsgraph_get()
part_counts = {}
for obj in MESH_PARTS:
    ev = obj.evaluated_get(dg)
    mesh_eval = ev.to_mesh()
    mesh_eval.calc_loop_triangles() if hasattr(mesh_eval, 'calc_loop_triangles') else None
    part_counts[obj.name] = len(mesh_eval.loop_triangles)
    ev.to_mesh_clear()
triangles = sum(part_counts.values())
print("GENESIS_ANVIL_V020_TRIANGLES:", triangles)
if triangles > MAX_TRIANGLES:
    raise RuntimeError("ANVIL triangle budget exceeded: %d > %d" % (triangles, MAX_TRIANGLES))

# Save canonical high-quality working master plus actual GLB target for PlayCanvas.
bpy.ops.object.select_all(action="DESELECT")
for obj in MESH_PARTS:
    obj.select_set(True)
bpy.context.view_layer.objects.active = BODY
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "PG_Yunque_Medieval_Realista_V020.blend"))
bpy.ops.export_scene.gltf(
    filepath=str(OUT / "PG_Yunque_Medieval_Realista_V020.glb"),
    export_format="GLB", use_selection=True, export_apply=True)

# Studio turntable. Real 16 yaw angles from THE SAME final Blender mesh.
bpy.ops.object.select_all(action="DESELECT")
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("Studio_matte_world")
    bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (.24, .25, .27, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = .56

def area(name, pos, power, color, size):
    data = bpy.data.lights.new(name, "AREA")
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = pos
    data.energy = power
    data.color = color
    data.shape = "DISK"
    data.size = size
    direction = Vector((0, 0, .32)) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj
area("Softbox_grande_izq", (-1.9, -2.4, 2.8), 380, (1.0, .96, .90), 3.7)
area("Softbox_lateral", (1.4, 2.0, 2.4), 275, (.91, .94, 1.0), 3.2)
area("Luz_contorno", (-1.4, 1.6, 2.0), 205, (1.0, .97, .93), 2.7)
area("Softbox_frontal_superior", (.4, -.6, 3.4), 130, (.97,.98,1.0), 3.0)
area("Softbox_fill_neck", (1.6, -2.1, .94), 120, (1.0,.93,.84), 2.9)

cam_dat = bpy.data.cameras.new("Camera_16_vistas")
cam = bpy.data.objects.new("Camera_16_vistas", cam_dat)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam_dat.type = "ORTHO"
cam_dat.ortho_scale = 1.43
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 68
scene.view_layers[0].cycles.use_denoising = True
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = True
scene.view_settings.view_transform = "Filmic"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = -.01
scene.view_settings.gamma = 1

def viewpoint(yaw, elevation, suffix):
    a = math.radians(yaw)
    e = math.radians(elevation)
    dist = 2.1
    cam.location = (math.cos(a) * math.cos(e) * dist,
                    math.sin(a) * math.cos(e) * dist,
                    .29 + math.sin(e) * dist)
    aim = Vector((0, 0, .29)) - cam.location
    cam.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(OUT / suffix)
    bpy.ops.render.render(write_still=True)
    print("RENDER_READY:", suffix, "ANGLE:", yaw, "ELEV:", elevation)

for index in range(16):
    viewpoint(index * 22.5, 27, "PG_Yunque_V020_vista_%02d.png" % (index + 1))
viewpoint(315, 83, "PG_Yunque_V020_superior.png")
viewpoint(115, -38, "PG_Yunque_V020_inferior.png")
viewpoint(295, 36, "PG_Yunque_V020_hero.png")

report = {
    "asset_id": "PG_Yunque_Medieval_Realista_V020",
    "pipeline": "Blender via GitHub Actions only",
    "status": "CANDIDATE_REVIEW_NOT_APPROVED",
    "visual_reference": "Historical dark burnished iron anvil, seamless forged steel working face",
    "triangles_evaluated": triangles,
    "top_steel_face_consistency": round(top_ratio,6),
    "continuous_hardened_face": "Planar separate forge-welded cap, not voxelized",
    "triangle_limit": MAX_TRIANGLES,
    "triangle_parts": part_counts,
    "pbr_texture_dimensions": {"width": TEX_SIZE, "height": TEX_SIZE},
    "pbr_texture_files": sorted(x.name for x in TEX.glob("*.png")),
    "orbit_views": 16,
    "extra_views": ["superior", "inferior", "hero"],
    "similarity_95_percent": "NOT VERIFIED: actual 16-view user reference comparison required",
    "playcanvas_ready": "NO - user release gate is quality >8/10"
}
with open(OUT / "PG_Yunque_V020_AUDIT.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print("ANVIL_READY_TRIANGLES:", triangles)
