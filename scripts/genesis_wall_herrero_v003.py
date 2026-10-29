# Project Genesis / PlayCanvas - Herrero exterior wall V003.
# Generator executed ONLY in public GitHub Actions with Blender 4.5.13 LTS.
# Source PBR scans: Poly Haven rock_05 and weathered_planks (CC0).
# This is an experimental art candidate, NEVER an approved game asset.
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
import numpy as np

SEED = 10292026
random.seed(SEED)
ROOT = Path("output_workshop_wall_herrero_v003").resolve()
ROOT.mkdir(parents=True, exist_ok=True)
INPUT = Path("inputs/wall_herrero_v003").resolve()
W, H, THICK = 7.875, 3.20, 0.43
DOOR_W, DOOR_H = 1.48, 2.43
ASSET_PREFIX = "WALL_"
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)

def img_load(path, color):
    img = bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return img

def tone_scan(filename, multipliers, dest):
    src = img_load(INPUT / filename, True)
    w, h = src.size[:]
    array = np.empty(w*h*4, dtype=np.float32)
    src.pixels.foreach_get(array)
    rgba = array.reshape((h*w, 4))
    for c in range(3):
        rgba[:,c] = np.clip(rgba[:,c] * multipliers[c], 0.0, 1.0)
    out = bpy.data.images.new(dest, width=w, height=h, alpha=False, float_buffer=False)
    out.pixels.foreach_set(array)
    out.filepath_raw = str(ROOT / (dest+".jpg"))
    out.file_format = "JPEG"
    out.save()
    out.colorspace_settings.name = "sRGB"
    del array, rgba
    return out

def pbr_material(label, base_image, rough_img, normal_img, rough_bias=0):
    mat = bpy.data.materials.new(label)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.86 + rough_bias
    color = nodes.new("ShaderNodeTexImage")
    color.name = "CC0 Scanned Albedo"
    color.image = base_image
    links.new(color.outputs["Color"], bsdf.inputs["Base Color"])
    rough = nodes.new("ShaderNodeTexImage")
    rough.name = "CC0 Scanned Roughness"
    rough.image = rough_img
    links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
    normal = nodes.new("ShaderNodeTexImage")
    normal.name = "CC0 Scanned Normal OpenGL"
    normal.image = normal_img
    nm = nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.05
    links.new(normal.outputs["Color"], nm.inputs["Color"])
    links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

stone_albedo = tone_scan("stone_albedo_2k.jpg", (.46,.47,.49), "herrero_stone_charcoal_albedo_2k")
wood_albedo = tone_scan("wood_albedo_2k.jpg", (.34,.29,.25), "herrero_oak_smoke_albedo_2k")
stone_rough = img_load(INPUT / "stone_rough_2k.jpg", False)
stone_normal = img_load(INPUT / "stone_normal_2k.jpg", False)
wood_rough = img_load(INPUT / "wood_rough_2k.jpg", False)
wood_normal = img_load(INPUT / "wood_normal_2k.jpg", False)
height_img = img_load(INPUT / "stone_height_2k.png", False)
stone = pbr_material("Herrero_PBR_Scanned_Weathered_Limestone_Charcoal", stone_albedo, stone_rough, stone_normal)
oak = pbr_material("Herrero_PBR_Weathered_Oak_Smoke", wood_albedo, wood_rough, wood_normal)
iron = bpy.data.materials.new("Herrero_PBR_Forged_Iron_Oxide")
iron.diffuse_color = (.075,.073,.071,1)
iron.use_nodes=True
ibs = iron.node_tree.nodes.get("Principled BSDF")
ibs.inputs["Base Color"].default_value=(.075,.073,.071,1)
ibs.inputs["Metallic"].default_value=.72
ibs.inputs["Roughness"].default_value=.77
mortar = bpy.data.materials.new("Herrero_Dark_Lime_Mortar")
mortar.use_nodes=True
mbs=mortar.node_tree.nodes.get("Principled BSDF")
mbs.inputs["Base Color"].default_value=(.11,.105,.095,1)
mbs.inputs["Roughness"].default_value=.97

# The scanned stone displacement is sampled to create physical relief, rather
# than showing a completely flat quad with a "rock-looking" color.
pix = np.empty(height_img.size[0]*height_img.size[1]*4, dtype=np.float32)
height_img.pixels.foreach_get(pix)
height_map = pix.reshape((height_img.size[1], height_img.size[0], 4))[:,:,0]
im_w, im_h = height_img.size[0], height_img.size[1]
def pbr_uv(x,z):
    return ((x+W/2.0)/3.10, z/2.90)
def relief(x,z):
    u,v=pbr_uv(x,z)
    ix=int((u%1.0)*(im_w-1)); iz=int((v%1.0)*(im_h-1))
    h=float(height_map[iz,ix])
    return .087*(h-.5)+.013*math.sin(12*x+7*z)*math.sin(16*z-3*x)

def box(label, center, dims, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    ob=bpy.context.object; ob.name=ASSET_PREFIX+label
    ob.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    if bevel:
        mod=ob.modifiers.new("Natural eased work-worn edges","BEVEL")
        mod.width=bevel;mod.segments=2
        if hasattr(mod,"affect"): mod.affect="EDGES"
        mod2=ob.modifiers.new("Preserve face normals","WEIGHTED_NORMAL")
    return ob

# Use real vertex displacement and a continuous stone-wall UV across the
# doorway. The doorway is an actual empty opening, not a black rectangle.
def clip_cell(poly, sx, sz, nx, nz):
    # Voronoi half plane: points nearer (sx,sz) than (nx,nz).
    a=nx-sx; b=nz-sz
    c=.5*(nx*nx+nz*nz-sx*sx-sz*sz)
    result=[]
    if not poly:return []
    for idx in range(len(poly)):
        p=poly[idx-1];q=poly[idx]
        fp=a*p[0]+b*p[1]-c
        fq=a*q[0]+b*q[1]-c
        pin=fp<=0; qin=fq<=0
        if pin!=qin:
            t=fp/(fp-fq) if abs(fp-fq)>1e-9 else .5
            result.append((p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t))
        if qin:result.append(q)
    return result

def facing_panel(label,x0,x1,z0,z1):
    # Real irregular quarried stones. The base is a true dark mortar gap,
    # while individual relief shells have different front depths.
    # The cells are clipped to exact panel bounds to preserve V011 cutout.
    seed=random.Random(3107+len(label)*13)
    dx,dz=.31,.255
    centers=[]
    ncols=int((x1-x0)/dx)+5;nrows=int((z1-z0)/dz)+5
    for iz in range(-2,nrows):
        for ix in range(-2,ncols):
            x=x0+(ix+.5+(iz%2)*.43)*dx+seed.uniform(-.086,.086)
            z=z0+(iz+.5)*dz+seed.uniform(-.066,.066)
            if x0-.42<x<x1+.42 and z0-.35<z<z1+.35:
                centers.append((x,z))
    verts=[];uv_coords=[];faces=[];smooth=[]
    stone_count=0
    for sx,sz in centers:
        poly=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
        neighbors=sorted(((nx-sx)**2+(nz-sz)**2,nx,nz) for nx,nz in centers
                         if (nx, nz)!=(sx,sz))[:21]
        for _,nx,nz in neighbors:
            poly=clip_cell(poly,sx,sz,nx,nz)
            if len(poly)<3:break
        if len(poly)<3:continue
        twice_area=sum(poly[i][0]*poly[(i+1)%len(poly)][1]-
                       poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))
        if abs(twice_area)<.014:continue
        cx=sum(p[0] for p in poly)/len(poly)
        cz=sum(p[1] for p in poly)/len(poly)
        # Inset each unique rock creates a physical 1-2cm mortar crevice.
        inset=seed.uniform(.011,.018)
        shell=[]
        for x,z in poly:
            diff=Vector((cx-x,cz-z))
            if diff.length>.0001:
                diff.normalize()
                x+=diff.x*inset;z+=diff.y*inset
            # Nonplanar chipped front, tracked over the real PBR scan.
            front_y=-THICK*.5-.019-seed.uniform(.0,.023)-relief(x,z)*.43
            shell.append((x,front_y,z))
        center_y=-THICK*.5-.052-seed.uniform(0,.040)-relief(cx,cz)*.6
        base=len(verts)
        verts.append((cx,center_y,cz));uv_coords.append(pbr_uv(cx,cz))
        for p in shell:
            verts.append(p);uv_coords.append(pbr_uv(p[0],p[2]))
        for x,y,z in shell:
            verts.append((x,-THICK*.5+.008,z));uv_coords.append(pbr_uv(x,z))
        n=len(shell)
        for j in range(n):
            faces.append((base,base+1+j,base+1+(j+1)%n));smooth.append(True)
            faces.append((base+1+j,base+n+1+j,base+n+1+(j+1)%n,
                          base+1+(j+1)%n));smooth.append(False)
        stone_count+=1
    mesh=bpy.data.meshes.new(label+"_hand_set_irregular_quarry_stones")
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(ASSET_PREFIX+label+"_actual_masonry",mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(stone)
    uv=mesh.uv_layers.new(name="UVMap")
    for face,sm in zip(mesh.polygons,smooth):
        face.use_smooth=sm
        for li in face.loop_indices:
            uv.data[li].uv=uv_coords[mesh.loops[li].vertex_index]
    print("ACTUAL_VORONOI_STONES",label,stone_count,"triangles",len(faces))
    return obj

doorhalf=DOOR_W/2
for label,x0,x1,z0,z1 in [
    ("StoneLeft",-W/2,-doorhalf,0,H),
    ("StoneRight",doorhalf,W/2,0,H),
    ("StoneLintel",-doorhalf,doorhalf,DOOR_H,H)]:
    box(label+"_backing",((x0+x1)/2,0,(z0+z1)/2),(x1-x0,THICK,z1-z0),mortar)
    facing_panel(label+"_relief",x0,x1,z0,z1)

# The bottom foundation is rough quarry stone, not a regular brick pattern.
# Unlike repeating cube walls, each stone is individually warped.
def quarry_rock(label, center, radii, material, seed):
    rng=random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=center)
    ob=bpy.context.object;ob.name=ASSET_PREFIX+label
    for v in ob.data.vertices:
        p=v.co
        jag=rng.uniform(.87,1.16)
        p.x*=radii[0]*jag
        p.y*=radii[1]*rng.uniform(.85,1.16)
        p.z*=radii[2]*rng.uniform(.80,1.17)
        if p.y < 0: p.y*=.72
    ob.data.materials.append(material)
    return ob

# V003: natural broken-stone cells replace the synthetic sphere foundation.
# Massive oak framing, bolted into real stone. Avoid generic uniformly
# spaced wall cubes. The jamb fits AROUND the door V011 opening.
for side in (-1,1):
    box("OakCornerPost_"+str(side),(side*(W/2-.14),-.27,1.60),(.26,.36,3.14),oak,.018)
    box("OakDoorJamb_"+str(side),(side*(doorhalf+.115),-.32,DOOR_H*.5),
        (.17,.32,DOOR_H),oak,.016)
box("OakMainHeadBeam",(0,-.30,H-.115),(W-.33,.33,.225),oak,.022)
box("OakDoorLintel",(0,-.34,DOOR_H+.103),(DOOR_W+.58,.37,.208),oak,.018)
for side in (-1,1):
    bx=side*2.50
    ob=box("IronTieBase_"+str(side),(bx,-.403,H-.20),(.23,.075,.29),iron,.008)
    for n in range(2):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=.029,
                  location=(bx+(.065 if n else -.065),-.45,H-.20))
        stud=bpy.context.object;stud.name=ASSET_PREFIX+"Rivet_"+str(side)+"_"+str(n)
        stud.data.materials.append(iron)
# Structurally legible little returns on each end, NOT whole new buildings.
# V003 keeps the standalone wall thin; avoid unnatural side-return slabs.

# Review stage; never include it in the GLB.
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.03))
ground=bpy.context.object;ground.name="REVIEW_Ground"
ground.scale=(7.0,3.8,1)
gm=bpy.data.materials.new("ReviewNeutralGravel");gm.diffuse_color=(.23,.21,.19,1)
gm.use_nodes=True
gm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(.23,.21,.19,1)
ground.data.materials.append(gm)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)

world=bpy.context.scene.world
world.color=(.15,.17,.20)
def area(name, location, strength, size):
    ld=bpy.data.lights.new(name,"AREA");ld.energy=strength;ld.shape="DISK";ld.size=size
    ob=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(ob)
    ob.location=location
    ob.rotation_euler=(Vector((0,0,1.5))-ob.location).to_track_quat("-Z","Y").to_euler()
area("REVIEW_KeySoftbox",(-3,-5,7),1250,6)
area("REVIEW_Fill",(5,-3,4),760,5)
area("REVIEW_Rim",(1,4,6),920,4)
bpy.ops.object.camera_add(location=(10,-16,6))
cam=bpy.context.object;cam.name="REVIEW_Camera"
cam.data.type='ORTHO';cam.data.ortho_scale=9.7
bpy.context.scene.camera=cam
sc=bpy.context.scene
sc.render.engine='CYCLES'
sc.cycles.samples=40
bpy.context.view_layer.cycles.use_denoising=True
sc.render.image_settings.file_format='PNG'
sc.render.resolution_x=1400;sc.render.resolution_y=900
sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX'
sc.render.film_transparent=False

# GLB only contains genuine wall geometry, with scanned PBR textures.
bpy.ops.object.select_all(action='DESELECT')
objects=[ob for ob in bpy.context.scene.objects if ob.name.startswith(ASSET_PREFIX) and ob.type=='MESH']
for ob in objects: ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.gltf(filepath=str(ROOT/"genesis_wall_herrero_v003.glb"),
                           export_format='GLB',use_selection=True,export_texcoords=True,
                           export_normals=True,export_materials='EXPORT')
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"genesis_wall_herrero_v003.blend"))
def camera_at(position, target, scale):
    cam.location=position
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.ortho_scale=scale
shots=[
    ("front",(0,-15,4.0),(0,0,1.6),9.0),
    ("three_quarter",(9,-13,6.1),(0,0,1.45),9.8),
    ("side",(11,-5,5.4),(0,0,1.45),9.4),
    ("detail",(-1.85,-4.0,2.75),(-2.1,0,1.65),4.3)]
for label,position,target,scale in shots:
    camera_at(position,target,scale)
    sc.render.filepath=str(ROOT/(label+".png"))
    bpy.ops.render.render(write_still=True)
tris=sum(len(p.vertices)-2 for ob in objects for p in ob.data.polygons)
audit={
 "asset":"ProjectGenesis_Herrero_ExteriorWall_V003",
 "status":"EXPERIMENTAL_NOT_APPROVED",
 "actual_workshop_front_reference_m":W,
 "wall_height_m":H,
 "door_cutout_m":[DOOR_W,DOOR_H],
 "stone_height_displacement":"clipped Voronoi individual stone relief + scanned PBR height",
 "scanned_materials":["polyhaven/rock_05","polyhaven/weathered_planks"],
 "license":"CC0",
 "render_views":[s[0] for s in shots],
 "mesh_count":len(objects),
 "triangles":tris,
 "glb_bytes":(ROOT/"genesis_wall_herrero_v003.glb").stat().st_size,
 "generator_seed":SEED,
 "texture_resolution":2048,
 "geometry_approval":"NO",
 "visual_score":"pending human review",
 "notes":"Modular wall with hundreds of real irregular stones. V011 original door untouched."
}
(ROOT/"AUDIT.json").write_text(json.dumps(audit,indent=2))
print("GENESIS_HERRERO_WALL_COMPLETE",json.dumps(audit))
