# Door V011: real rear hinge-side reinforcement connections and legible metal QA.
# Blender 4.5 / PlayCanvas GLB; all scene generation runs in GitHub Actions.
import bpy, math, json, random
from math import sin, cos, pi
from pathlib import Path
from mathutils import Vector
import numpy as np

OUT=Path("output_blacksmith_door_art_080")
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
random.seed(26)

# Dimensions reference hero: width 1.2 m, max height 2.31 m, 0.104 m thick.
WIDTH=1.20
BASE=.036
SPRING=1.775
RISE=.525
FRONT=-.057
BACK=.057
CENTER_PEEP=1.52
HANDLE_Z=1.036

def recover_v175_atlas(path):
    source=bpy.data.images.load(str(Path(path).resolve()),check_existing=True)
    w,h=source.size
    rgba=np.empty(w*h*4,dtype=np.float32)
    source.pixels.foreach_get(rgba)
    pixels=rgba.reshape(h,w,4)[:,:,:3]
    # V175 source is an ingot-specific UV atlas: recover a continuous face region.
    # Never attach that atlas directly to door UVs, which would introduce false seams.
    patch=pixels[70:520,20:275,:].copy()
    return patch

V175_COLOR=None  # intentionally unused: new door plate material is independent
V175_ROUGH=None

# CC0 photogrammetric rust substrate is used ONLY for physical surface detail.
# The original door panel shape, ornament and V175 ingot hue stay authoritative.
# Poly Haven: https://polyhaven.com/a/rust_coarse_01
def scan_pixels(filepath,linear=False):
    im=bpy.data.images.load(str(Path(filepath).resolve()),check_existing=True)
    if linear: im.colorspace_settings.name="Non-Color"
    width,height=im.size
    a=np.empty(width*height*4,dtype=np.float32)
    im.pixels.foreach_get(a)
    return a.reshape(height,width,4)[:,:,:3].copy()

SCAN_RUST_COLOR=None  # not imported for standalone door PBR
SCAN_RUST_ROUGH=None  # not imported for standalone door PBR
SCAN_RUST_NORMAL=None  # not imported for standalone door PBR
# CC0 scan of real weathered steel: independent color, roughness and GL normal layers.
SCAN_STEEL_COLOR=None  # not imported for standalone door PBR
SCAN_STEEL_ROUGH=None  # not imported for standalone door PBR
SCAN_STEEL_NORMAL=None  # not imported for standalone door PBR

def atlas_signal(patch,n,seed):
    # Continuous bilinear reflection sampling of the V175 ingot atlas.
    # Earlier nearest-neighbor lookup produced visible square pixels.
    hh,ww,_=patch.shape
    fy=np.linspace(0,hh*3-1,n,dtype=np.float32)
    fx=np.linspace(0,ww*4-1,n,dtype=np.float32)
    y0=np.floor(fy).astype(np.int32);x0=np.floor(fx).astype(np.int32)
    ty=(fy-y0)[:,None,None];tx=(fx-x0)[None,:,None]
    def mirror(idx,length):
        q=idx%(2*length)
        return np.minimum(q,2*length-1-q)
    y0m=mirror(y0,hh);y1m=mirror(y0+1,hh)
    x0m=mirror(x0,ww);x1m=mirror(x0+1,ww)
    a=patch[y0m[:,None],x0m[None,:],:]
    b=patch[y1m[:,None],x0m[None,:],:]
    c=patch[y0m[:,None],x1m[None,:],:]
    d=patch[y1m[:,None],x1m[None,:],:]
    return (a*(1-ty)*(1-tx)+b*ty*(1-tx)+c*(1-ty)*tx+d*ty*tx).astype(np.float32)

def material(name, base, metallic, roughness, seed):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*base,1)
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Metallic"].default_value=metallic
    bs.inputs["Roughness"].default_value=roughness
    n=2048  # V029 exploratory 2K multilayer preview
    rng=np.random.default_rng(seed)
    # Bilinear/smoothstep lattice noise removes the 12-pixel square mosaics of V003.
    def smooth_noise(grid):
        gx=np.linspace(0,grid-1,n,dtype=np.float32)
        ix=np.floor(gx).astype(np.int32)
        t=gx-ix;t=t*t*(3.-2.*t)
        jx=np.minimum(ix+1,grid-1)
        src=rng.standard_normal((grid,grid)).astype(np.float32)
        aa=src[ix[:,None],ix[None,:]]
        ab=src[jx[:,None],ix[None,:]]
        ba=src[ix[:,None],jx[None,:]]
        bb=src[jx[:,None],jx[None,:]]
        return aa*(1-t[:,None])*(1-t[None,:])+ab*t[:,None]*(1-t[None,:])+ba*(1-t[:,None])*t[None,:]+bb*t[:,None]*t[None,:]
    broad=smooth_noise(36)
    fine=smooth_noise(178)
    micro=rng.normal(0,1,(n,n)).astype(np.float32)
    cloud=np.clip(broad*.72+fine*.26,-1.8,1.8)
    scratches=np.clip(smooth_noise(320)*.15+micro*.075,-.18,.18)
    # V013: preserve largely blue-black wrought iron; oxidation lives in low-exposure
    # material groups and irregular recessed patches, not as a continuous brown paint.
    # Each channel is physically consistent: iron metallic, ferric patina rough/nonmetal.
    broad_oxide=smooth_noise(11)
    weather=np.clip(.68*broad+.30*broad_oxide+.21*fine,-2.2,2.2)
    oxide_seed=np.maximum(0.0, weather-.22)
    if "brass" in name:
        oxide=np.zeros_like(oxide_seed)
        ageing=.016
    elif "inset" in name:
        oxide=np.clip(.58*oxide_seed+.038*np.maximum(0,broad_oxide),0,.53)
        ageing=.064
    elif "worn_edges" in name or "highlights" in name:
        oxide=np.clip(.11*oxide_seed,0,.095)
        ageing=.009
    elif "hand_hammered_charcoal" in name:
        oxide=np.clip(.11*oxide_seed+.004*np.maximum(0,broad_oxide),0,.10)
        ageing=.012
    else:
        oxide=np.clip(.38*oxide_seed+.013*np.maximum(0,broad_oxide),0,.32)
        ageing=.019
    variation=np.clip(1+.42*broad+.15*fine+.16*scratches,.53,1.49)
    if "hand_hammered_charcoal" in name:
        variation=np.clip(1+.105*broad+.075*fine+.10*scratches,.84,1.16)
    elif "brass" in name:
        variation=np.clip(1+.11*broad+.06*fine,.84,1.13)
    # Subtle graphite/blue steel, visible only as specular texture variation.
    axis=np.linspace(0,1,n,dtype=np.float32)
    xx=axis[:,None];yy=axis[None,:]
    edge_distance=np.minimum(np.minimum(xx,1-xx),np.minimum(yy,1-yy))
    worn=np.exp(-edge_distance/.028)*(.26+.12*np.maximum(-cloud,0))
    rust_color=(.24,.105,.060)
    color=np.stack([np.clip(
        base[k]*variation*(1-ageing)*(1-.036*worn)
        + oxide*(rust_color[k]-base[k])
        + worn*(.024 if k==0 else (.029 if k==1 else .036)),
        0,1) for k in range(3)],axis=-1)
    # Layer 1: verified V175 ingot base-color/roughness samples (atlas-aware remap).
    # Layer 2: independent forged metal body. Layer 3: oxide and hammered microrelief.
    if "hand_hammered_charcoal" in name:
        source_col=atlas_signal(V175_COLOR,n,seed)
        # Lift atlas values slightly while retaining its ferric dark/brown palette.
        recovered=np.clip(.032+.43*(source_col-np.median(source_col,axis=(0,1))),.017,.16)
        color=np.clip(.62*color+.38*recovered,0,1)
        # Ferric oxide embedded into the SAME noise pattern, not added decals.
        ferric=np.clip(oxide*(.50+.70*np.maximum(fine,0)+.33*np.maximum(micro,0)),0,.62)
        color[:,:,0]=np.clip(color[:,:,0]+.035*ferric,0,1)
        color[:,:,1]=np.clip(color[:,:,1]+.008*ferric,0,1)
        color[:,:,2]=np.clip(color[:,:,2]-.036*ferric,0,1)
        source_rough=atlas_signal(V175_ROUGH,n,seed+71)[:,:,0]
    else:
        source_rough=None
    rough=np.clip(
        roughness-.065+.11*fine+.022*micro+.46*oxide+
        .035*np.maximum(0.0,-weather),.24,.91)
    if source_rough is not None:
        rough=np.clip(.78*rough+.22*source_rough+.024*fine,.24,.89)
    # Independent weathered-metal scan: real sheet scratches, rust freckles and
    # per-pixel roughness. Strip only high-frequency signal to avoid copying seams
    # or changing the V011 ornamental pattern. V175 retains master color identity.
    if "hand_hammered_charcoal" in name:
        sheet=SCAN_STEEL_COLOR
        mono=.34*sheet[:,:,0]+.51*sheet[:,:,1]+.15*sheet[:,:,2]
        surround=.25*(np.roll(mono,10,axis=0)+np.roll(mono,-10,axis=0)+
                       np.roll(mono,10,axis=1)+np.roll(mono,-10,axis=1))
        scan_micro=np.clip((mono-surround)*1.55,-.18,.18)
        color=np.clip(color*(1+2.4*scan_micro[:,:,None]),0,1)
        edge_scale=np.exp(-edge_distance/.056)*np.clip(.22+.7*np.maximum(broad_oxide,0),0,1)
        oxidized_pixels=np.clip((sheet[:,:,0]-sheet[:,:,2]-.008)*3.2,0,1)
        # Rust is strongest in edge crevices, with only fine freckles at the centre.
        oxidation=np.clip(oxidized_pixels*(.12+.98*edge_scale),0,.38)
        color=np.clip(color*(1-oxidation[:,:,None])+
                      oxidation[:,:,None]*np.array([.235,.105,.063],dtype=np.float32),0,1)
        rough=np.clip(.63*rough+.37*SCAN_STEEL_ROUGH[:,:,0]+.20*oxidation,.30,.82)
    metalness=np.clip(metallic*(1-2.45*oxide),.10,1.0)
    if "hand_hammered_charcoal" in name:
        metalness=np.clip(metalness-.62*oxidation,.12,1)
    # Local pitting belongs mainly to oxide; the surrounding forged metal stays fine.
    # NORMAL ONLY V080. The preceding albedo, metallic and roughness logic
    # is byte-for-byte unchanged relative to V029.
    bump=np.clip(.50+(.020 if "hand_hammered_charcoal" in name else .14)*cloud+.026*fine+.0024*micro+
                 .024*oxide*(.40+fine),0,1)
    if "iron_v028_hand_hammered_charcoal" in name:
        # Forged plate hammering in a separate height field; broad and fine
        # depressions that affect only tangent-space normals, not color.
        dents=np.zeros((n,n),dtype=np.float32)
        dent_rng=np.random.default_rng(175047)
        for _ in range(1350):
            cx=int(dent_rng.integers(18,n-18));cy=int(dent_rng.integers(18,n-18))
            radius=int(dent_rng.integers(11,35))
            aspect=float(dent_rng.uniform(.66,1.42))
            y0=max(0,cy-radius*2);y1=min(n,cy+radius*2+1)
            x0=max(0,cx-radius*2);x1=min(n,cx+radius*2+1)
            yy,xx=np.ogrid[y0:y1,x0:x1]
            rr=((xx-cx)/(radius*aspect))**2+((yy-cy)/radius)**2
            # Concave hammer strike with raised forged shoulder.
            local=-.13*np.exp(-rr*1.7)+.027*np.exp(-(rr-1.1)**2*2.2)
            dents[y0:y1,x0:x1]+=local.astype(np.float32)
        bump=np.clip(bump+dents,0,1)
        # 4K normal MASTER: color/roughness remain identical 2K V029 arrays.
        bump=np.repeat(np.repeat(bump,2,axis=0),2,axis=1)
    strength=5.8 if "iron_v028_hand_hammered_charcoal" in name else 2.4
    nx=-np.gradient(bump,axis=1)*strength
    ny=-np.gradient(bump,axis=0)*strength
    nz=np.ones_like(nx)
    lng=np.sqrt(nx*nx+ny*ny+nz*nz)
    normal=np.stack([.5+.5*nx/lng,.5+.5*ny/lng,.5+.5*nz/lng],axis=-1)
    if "hand_hammered_charcoal" in name:
        # Combine physically recorded pits (normal GL) with authored hammering.
        base_scan=SCAN_STEEL_NORMAL
        # True bilinear 2K -> 4K normal resampling (no nearest-neighbor pixels).
        scan_next_y=np.roll(base_scan,-1,axis=0)
        scan_next_x=np.roll(base_scan,-1,axis=1)
        scanned=np.empty((base_scan.shape[0]*2,base_scan.shape[1]*2,3),dtype=np.float32)
        scanned[::2,::2]=base_scan
        scanned[1::2,::2]=.5*(base_scan+scan_next_y)
        scanned[::2,1::2]=.5*(base_scan+scan_next_x)
        scanned[1::2,1::2]=.25*(base_scan+scan_next_y+scan_next_x+np.roll(scan_next_y,-1,axis=1))
        tex_vec=normal*2-1
        scan_vec=scanned*2-1
        mixed=tex_vec*.86+scan_vec*.30
        mixed[:,:,2]=np.maximum(mixed[:,:,2],.16)
        norm=np.maximum(np.linalg.norm(mixed,axis=-1,keepdims=True),1e-5)
        normal=np.clip(.5+.5*mixed/norm,0,1)
    def map_img(kind,rgb,linear):
        im=bpy.data.images.new(name+"_"+kind,width=rgb.shape[1],height=rgb.shape[0],alpha=True)
        rgba=np.concatenate([rgb.astype(np.float32),np.ones((rgb.shape[0],rgb.shape[1],1),dtype=np.float32)],axis=2)
        if linear: im.colorspace_settings.name="Non-Color"
        im.pixels.foreach_set(np.clip(rgba,0,1).ravel())
        im.filepath_raw=str(OUT/(name+"_"+kind+".png"))
        im.file_format="PNG"
        im.save()
        im.pack()
        return im
    c=map_img("albedo",color,False)
    r=map_img("roughness",np.repeat(rough[:,:,None],3,axis=2),True)
    b=map_img("normal",normal,True)
    met=map_img("metallic",np.repeat(metalness[:,:,None],3,axis=2),True)
    nodes=m.node_tree.nodes
    cl=nodes.new("ShaderNodeTexImage");cl.image=c
    rl=nodes.new("ShaderNodeTexImage");rl.image=r
    nl=nodes.new("ShaderNodeTexImage");nl.image=b
    ml=nodes.new("ShaderNodeTexImage");ml.image=met
    nm=nodes.new("ShaderNodeNormalMap");nm.inputs["Strength"].default_value=1.0 if "iron_v028_hand_hammered_charcoal" in name else .70
    links=m.node_tree.links
    links.new(cl.outputs["Color"],bs.inputs["Base Color"])
    links.new(rl.outputs["Color"],bs.inputs["Roughness"])
    links.new(ml.outputs["Color"],bs.inputs["Metallic"])
    links.new(nl.outputs["Color"],nm.inputs["Color"])
    links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    return m


def make_door_specific_4k_material():
    """V080: unmodified scanned CC0 4K PBR maps; keep V011 mesh."""
    source=Path("assets/door_herrero/materials/rusted_scratched_iron_4k")
    prefix="rusted-scratched-iron_4k_"
    names={"albedo":"color","normal":"normalgl","roughness":"roughness","metallic":"metalness","displacement":"displacement"}
    images={}
    for key,suffix in names.items():
        p=source/(prefix+suffix+".jpg")
        if not p.is_file():
            raise FileNotFoundError("Required actual 4K PBR map missing: "+str(p))
        img=bpy.data.images.load(str(p.resolve()),check_existing=True)
        if tuple(img.size)!=(4096,4096):
            raise RuntimeError("Reject resized/substitute scan "+str(p)+" size="+str(tuple(img.size)))
        if key!="albedo": img.colorspace_settings.name="Non-Color"
        images[key]=img
    m=bpy.data.materials.new("door_v079_rusted_scratched_iron_original_CC0_4k")
    m.use_nodes=True
    nodes=m.node_tree.nodes
    links=m.node_tree.links
    bs=nodes.get("Principled BSDF")
    bs.inputs["Metallic"].default_value=1.0
    bs.inputs["Roughness"].default_value=.6
    # V080: Dark iron smoke-grey base colour and softened normal amplitude. Real source detail remains intact.
    albedo_tex=nodes.new("ShaderNodeTexImage")
    albedo_tex.label="Original Meshy CC0 scan albedo 4K"
    albedo_tex.image=images["albedo"]
    smoke=nodes.new("ShaderNodeMixRGB")
    smoke.blend_type="MULTIPLY"
    smoke.label="Smoke grey tint ONLY — original relief and masks unchanged"
    smoke.inputs[0].default_value=1.0
    smoke.inputs[2].default_value=(.34,.35,.35,1.0)
    # V080: selective dark petroleum patina on oxidized regions only.
    # Grayscale forged metal must remain neutral (no global cyan hue shift).
    neutral=nodes.new("ShaderNodeHueSaturation")
    neutral.label="Original scanned metallic luminance, no cyan cast"
    neutral.inputs["Saturation"].default_value=0.45
    links.new(albedo_tex.outputs["Color"],neutral.inputs["Color"])
    hsv=nodes.new("ShaderNodeSeparateColor")
    hsv.mode="HSV"
    links.new(albedo_tex.outputs["Color"],hsv.inputs["Color"])
    mask=nodes.new("ShaderNodeMath")
    mask.operation="MULTIPLY"
    mask.use_clamp=True
    mask.inputs[1].default_value=0.42
    links.new(hsv.outputs[1],mask.inputs[0])
    petrol=nodes.new("ShaderNodeMixRGB")
    petrol.blend_type="MIX"
    petrol.label="Muted petroleum patina limited to existing oxidized flecks"
    petrol.inputs[2].default_value=(0.10,0.23,0.225,1.0)
    links.new(mask.outputs["Value"],petrol.inputs[0])
    links.new(neutral.outputs["Color"],petrol.inputs[1])
    links.new(petrol.outputs["Color"],smoke.inputs[1])
    links.new(smoke.outputs["Color"],bs.inputs["Base Color"])
    # Prevent source metalness/low roughness from washing the plate white under area lights.
    # Retain real scan variation, scale reflectivity and set roughness floor.
    for kind,socket in (("roughness","Roughness"),("metallic","Metallic")):
        t=nodes.new("ShaderNodeTexImage")
        t.label="Original CC0 scan — "+kind
        t.image=images[kind]
        if kind=="metallic":
            scaled=nodes.new("ShaderNodeMath");scaled.operation="MULTIPLY"
            scaled.inputs[1].default_value=0.58
            links.new(t.outputs["Color"],scaled.inputs[0])
            links.new(scaled.outputs["Value"],bs.inputs[socket])
        else:
            floor=nodes.new("ShaderNodeMath");floor.operation="MAXIMUM"
            floor.inputs[1].default_value=0.62
            links.new(t.outputs["Color"],floor.inputs[0])
            links.new(floor.outputs["Value"],bs.inputs[socket])
    normaltex=nodes.new("ShaderNodeTexImage")
    normaltex.image=images["normal"]
    normalnode=nodes.new("ShaderNodeNormalMap")
    normalnode.space="TANGENT"
    normalnode.inputs["Strength"].default_value=0.65
    links.new(normaltex.outputs["Color"],normalnode.inputs["Color"])
    links.new(normalnode.outputs["Normal"],bs.inputs["Normal"])
    # Original displacement map kept intact in the 4K source pack; no geometry
    # displacement in this material-isolation test, to preserve approved V011.
    return m, neutral, smoke, mask

iron,neutral,smoke,mask=make_door_specific_4k_material()
edge=material("iron_v028_steel_worn_edges",(.048,.052,.055),.82,.78,18)
copper=material("copper_brass_v028_patinated",(.135,.097,.065),.82,.66,19)
shade=material("iron_v028_heat_darkened_recesses",(.091,.088,.083),.80,.76,20)
objects=[]
def keep(o):
    objects.append(o)
    return o
def bevel(o,w=.006,seg=2):
    a=o.modifiers.new("Light catches forged edge","BEVEL")
    a.width=w;a.segments=seg
    o.modifiers.new("Normals","WEIGHTED_NORMAL")
    return o
def cube(name,loc,dim,mat,w=.006):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name
    o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if w:bevel(o,w)
    return keep(o)
def cylinder(name,loc,r,d,mat,orientation=(0,0,0),verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc,rotation=orientation)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat);bevel(o,min(.004,r*.12),1)
    return keep(o)
def stroke(name,coords,rad,mat,closed=False):
    c=bpy.data.curves.new(name,"CURVE");c.dimensions="3D"
    c.bevel_depth=rad;c.bevel_resolution=2;c.resolution_u=12
    s=c.splines.new("POLY");s.points.add(len(coords)-1)
    for point,xyz in zip(s.points,coords):point.co=(*xyz,1)
    s.use_cyclic_u=closed
    ob=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return keep(ob)
def ring(name,x,z,r,y,thick,mat):
    return stroke(name,[(x+r*cos(2*pi*k/64),y,z+r*sin(2*pi*k/64)) for k in range(64)],thick,mat,True)
def scroll(name,x,z,r,turns,direction,yy,mat):
    coords=[]
    for i in range(72):
        t=i/71
        a=turns*2*pi*t
        radius=r*(1-.92*t)
        coords.append((x+direction*radius*cos(a),yy,z+radius*sin(a)))
    obj=stroke(name,coords,.009,mat)
    for idx,p in enumerate(obj.data.splines[0].points):
        p.radius=max(.13,1-idx/(len(coords)-1)*.79)
    return obj
def rivet(x,z,y=-.115,r=.013):
    rr=r*random.uniform(.86,1.11)
    cylinder("Irregular peened forge rivet",(x,y,z),rr,.010,copper if r<.010 else edge,(pi/2,0,0),12)

# Robust manifold quad-strip leaf: 40 continuous iron sections, not a fragile N-gon.
# Previous V001 lost its right-side fill after boolean; V002 has explicit camera-facing quads.
NSTRIPS=40
xs=[-.585+1.17*i/NSTRIPS for i in range(NSTRIPS+1)]
tops=[SPRING+RISE*math.sqrt(max(0,1-(x/.585)**2)) for x in xs]
outline=[(-.585,BASE),(.585,BASE)]+[(.585*math.cos(pi*k/96),SPRING+RISE*math.sin(pi*k/96)) for k in range(97)]
verts=[]
for y in (FRONT,BACK):
    for x,z in zip(xs,tops): verts.extend(((x,y,BASE),(x,y,z)))
def v(side,col,upper):
    return side*(2*(NSTRIPS+1))+col*2+int(upper)
faces=[]
for i in range(NSTRIPS):
    faces.append((v(0,i,0),v(0,i+1,0),v(0,i+1,1),v(0,i,1))) # front
    faces.append((v(1,i,0),v(1,i,1),v(1,i+1,1),v(1,i+1,0))) # rear
    faces.append((v(0,i,1),v(0,i+1,1),v(1,i+1,1),v(1,i,1))) # arched cap
    faces.append((v(1,i,0),v(1,i+1,0),v(0,i+1,0),v(0,i,0))) # lower edge
faces.extend(((v(0,0,0),v(0,0,1),v(1,0,1),v(1,0,0)),
              (v(1,NSTRIPS,0),v(1,NSTRIPS,1),v(0,NSTRIPS,1),v(0,NSTRIPS,0))))
mesh=bpy.data.meshes.new("Closed_arched_iron_leaf_quad_strips")
mesh.from_pydata(verts,[],faces);mesh.update(calc_edges=True)
door=bpy.data.objects.new("Door_arched_iron_body",mesh)
bpy.context.collection.objects.link(door)
door.data.materials.append(iron);keep(door)
# A genuine cut-through peephole; the shutter and surround are separately meshed.
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.063,depth=.35,
    location=(.0,0,CENTER_PEEP),rotation=(pi/2,0,0))
cutter=bpy.context.object
bpy.context.view_layer.objects.active=door
boolean=door.modifiers.new("Open peephole through plate","BOOLEAN")
boolean.operation="DIFFERENCE";boolean.object=cutter
bpy.ops.object.modifier_apply(modifier=boolean.name)
bpy.data.objects.remove(cutter,do_unlink=True)
# No invisible missing sections: every sample across the physical leaf MUST intersect.
# Peephole itself MUST be open and must not be filled by the steel body.
for testx,testz in ((-.44,.9),(-.21,1.05),(0,.9),(.21,1.05),(.44,.9),
                    (-.43,1.67),(.40,1.65),(0,2.13)):
    hit,_,_,_=door.ray_cast(Vector((testx,-.4,testz)),Vector((0,1,0)),distance=1)
    assert hit,("MISSING_DOOR_SURFACE",testx,testz)
hit,_,_,_=door.ray_cast(Vector((0,-.4,CENTER_PEEP)),Vector((0,1,0)),distance=1)
assert not hit,"PEEPHOLE_MUST_BE_OPEN"
bevel(door,.011)
# Machine-made shape rejected: asymmetric, smoothly rolled hand-forged inner and outer rim.
stroke("Outer_arch_rolled_rim",[(x,-.081,z) for x,z in outline],.020,edge,True)
stroke("Inner_arch_raised_bead",[(x*.927,-.090,BASE+(z-BASE)*.958) for x,z in outline],.006,edge,True)
# Subdivided slightly warped forge plates, not perfectly planar manufactured slabs.
def hammered_plate(name,z,height):
    cols,rows=15,11
    vs=[]
    for frontside,basey in enumerate((-.096,-.073)):
        for iz in range(rows+1):
            zz=z+(iz/rows-.5)*height
            for ix in range(cols+1):
                xx=(ix/cols-.5)*.817
                # Non-periodic hand-forged stretch waves; 2mm relief is enough.
                grain=.0026*math.sin(xx*19+zz*8)+.0020*math.sin(xx*41-zz*23)+.0011*math.sin(xx*76+zz*36)
                vs.append((xx,basey+grain,zz))
    one=(cols+1)*(rows+1)
    def v(side,ix,iz):return side*one+iz*(cols+1)+ix
    fs=[]
    for side in (0,1):
        for iz in range(rows):
            for ix in range(cols):
                ids=(v(side,ix,iz),v(side,ix+1,iz),v(side,ix+1,iz+1),v(side,ix,iz+1))
                fs.append(tuple(reversed(ids)) if side else ids)
    for ix in range(cols):
        for iz in (0,rows):
            fs.append((v(0,ix,iz),v(1,ix,iz),v(1,ix+1,iz),v(0,ix+1,iz)))
    for iz in range(rows):
        for ix in (0,cols):
            fs.append((v(0,ix,iz),v(0,ix,iz+1),v(1,ix,iz+1),v(1,ix,iz)))
    me=bpy.data.meshes.new(name+"_warped_iron")
    me.from_pydata(vs,[],fs);me.update()
    ob=bpy.data.objects.new(name,me)
    bpy.context.collection.objects.link(ob);ob.data.materials.append(iron)
    keep(ob);bevel(ob,.004,1)
    for polygon in me.polygons: polygon.use_smooth=True
    return ob

# Three genuinely recessed wrought-iron panels with shadow borders.
for i,(z0,z1) in enumerate(((.172,.655),(.725,1.285),(1.352,1.748))):
    h=z1-z0;z=(z1+z0)/2
    cube("Deep_sharp_shadow_inset_%d"%i,(0,-.064,z),(.855,.018,h),shade,.014)
    hammered_plate("Hand-hammered_twisted_sheet_%d"%i,z,h-.040)
    for sx in (-1,1):
        cube("Forged_panel_vertical_lip",(sx*.438,-.104,z),(.017,.036,h-.005),edge,.004)
    for zz in (z0,z1):
        cube("Forged_panel_horizontal_lip",(0,-.104,zz),(.877,.036,.019),edge,.004)
    for sx in (-1,1):
        for zz in (z0+.056,z1-.056):rivet(sx*.374,zz,-.116,.012)
# Six riveted shoulder and base forged rails
for z in (.11,1.805):
    cube("Heavy_merchant_shop_crossbar",(0,-.090,z),(1.036,.056,.056),edge,.009)
    for x in (-.49,-.24,0,.24,.49):rivet(x,z,-.130,.011)
# Riveted perimeter, natural rounded arch.
for side in (-1,1):
    for k in range(12):rivet(side*.533,.105+k*.149,-.101,.013)
for k in range(19):
    theta=pi*k/18
    rivet(.523*cos(theta),SPRING+.47*sin(theta),-.109,.012)
# Upper forged-scroll identity: mirror paired curled iron.
for side in (-1,1):
    scroll("Upper_outer_merchant_scroll",side*.25,2.01,.117,1.12,-side,-.108,edge)
    scroll("Upper_small_merchant_scroll",side*.382,1.982,.060,.95,side,-.115,edge)
    stroke("Upper_sweeping_arch_vine",[
        (side*(.025+.465*t/70),-.111,1.99+.14*sin(pi*t/70))
        for t in range(71)],.012,edge)
# Little central anvil-inspired leaf motif, forged not a heraldic castle emblem.
stroke("Arch_centre_leaf",[(-.036,-.122,2.06),(0,-.123,2.145),(.036,-.122,2.06)],.010,edge)
# Lower forged scrolls, recessed within last metal panel.
for side in (-1,1):
    scroll("Lower_shop_scroll",side*.23,.36,.12,1.12,-side,-.114,edge)
    scroll("Lower_end_scroll",side*.39,.36,.056,.86,side,-.113,edge)
    stroke("Lower_scroll_sweeping_base",[
        (side*(.036+.43*t/75),-.116,.33+.105*sin(pi*t/75)) for t in range(76)],.009,edge)
# Hinges: two decorative leaf shaped straps on left, with actual barrel and riveted pins.
for z in (.455,1.295):
    cylinder("Functional_vertical_hinge_barrel",(-.603,-.008,z),.036,.184,edge,verts=20)
    for dz in (-.086,.086):
        cylinder("Handforge_hinge_collar",(-.603,-.008,z+dz),.047,.019,iron,verts=20)
    poly=[(-.573,z-.054),(-.46,z-.054),(-.28,z-.036),(-.165,z-.019),
          (-.115,z),(-.165,z+.019),(-.28,z+.036),(-.46,z+.054),(-.573,z+.054)]
    n=len(poly)
    vs=[(x,y,h) for y in (-.125,-.10) for x,h in poly]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    fs += [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
    m=bpy.data.meshes.new("Hinge_spear_leaf")
    m.from_pydata(vs,[],fs);m.update()
    o=bpy.data.objects.new("Functional_riveted_hinge_strap",m)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(edge);keep(o);bevel(o,.005)
    for xx in (-.46,-.31,-.20):rivet(xx,z,-.141,.014)
# True ring for the central opening (clear centre) and an open side-flap on a separate pivot.
ring("Peephole_rich_brass_ring",0,CENTER_PEEP,.092,-.131,.016,copper)
ring("Peephole_engraved_inner_bead",0,CENTER_PEEP,.072,-.144,.004,edge)
for k in range(8):
    a=2*pi*k/8
    rivet(.088*cos(a),CENTER_PEEP+.088*sin(a),-.147,.008)
# Lid can be rotated to close; visual scene shows it opened to left.
flap_pivot=Vector((-.108,-.149,CENTER_PEEP))
cylinder("Peephole_lid_open",(-.194,-.166,CENTER_PEEP),.065,.015,copper,(pi/2,0,0),32)
ring("Peephole_lid_ridge",-.194,CENTER_PEEP,.056,-.179,.005,edge)
for dz in (-.038,.038):
    cylinder("Peephole_lid_vertical_pivot",(-.108,-.150,CENTER_PEEP+dz),.011,.038,edge,verts=12)
# ONE practical copper-brass LEVER on the right: shaft and handle are independent.
cube("Right_handle_copper_mount",(.454,-.110,HANDLE_Z),(.088,.028,.102),copper,.014)
cylinder("Right_handle_pivot_hub",(.454,-.145,HANDLE_Z),.037,.056,copper,(pi/2,0,0),32)
stroke("One_right_brass_horizontal_turning_lever",[(.443,-.184,HANDLE_Z),(.365,-.200,HANDLE_Z),
(.270,-.201,HANDLE_Z+.004),(.232,-.195,HANDLE_Z+.006)],.022,copper)
cylinder("One_lever_end_finish",(.232,-.195,HANDLE_Z+.006),.024,.025,copper,(0,pi/2,0),24)
# Selective hand-struck surface dents on four exposed iron panels (no crude tiled stones).
for zcentre,height in ():  # V080 remove 45 unwanted floating hair-like scar meshes
    for k in range(15):
        x=random.uniform(-.34,.34)
        z=zcentre+random.uniform(-height*.42,height*.42)
        if (x*x+(z-CENTER_PEEP)**2)<.020: continue
        y=-.100-random.uniform(.001,.003)
        ln=random.uniform(.008,.027)
        stroke("Irregular_short_hammer_scar",[(x-ln/2,y,z-.0008),(x+ln/2,y,z+.0008)],
            random.uniform(.00056,.0011),shade)
# Brass is patinated; pin heads vary in size and are not ornamental copper dots.
# Functional key escutcheon below turning lever.
cube("Hand-wrought lock cover plate",(.435,-.117,.897),(.062,.018,.109),edge,.009)
cube("Actual deep keyway shadow",(.435,-.130,.909),(.010,.004,.051),shade,.002)
cylinder("Keyhole bowl",(.435,-.131,.938),.010,.004,shade,(math.pi/2,0,0),16)
# V008 X-braces ended in open air, above/below the actual horizontal rails.
# V011 extends all four diagonal ends INTO the upper/lower structural straps
# and adds peened anchor plates so the rear stiffeners are mechanically held.
for z in (.225,.940,1.815):
    cube("Interior_forged_crossbrace",(0,.090,z),(1.02,.038,.056),iron,.006)
for side in (-1,1):
    stroke("Interior_diagonal_stiffener",[
        (side*.46,.116,.224),(-side*.46,.116,1.815)],.021,iron)
    for x,z in ((side*.46,.224),(-side*.46,1.815)):
        cube("Structural_rear_brace_end_plate",(x,.133,z),(.095,.025,.071),edge,.008)
        cylinder("Peened_rear_brace_to_rail_anchor",(x,.152,z),.016,.012,copper,
                 (pi/2,0,0),20)
cube("Interior_lock_case",(.44,.11,HANDLE_Z),(.17,.064,.23),edge,.010)

# An export hierarchy built for a hinge-animated GLB.
root=bpy.data.objects.new("DoorRoot_animate_rotation_about_left_vertical_axis",None)
bpy.context.collection.objects.link(root)
root.location=(-.603,0,0)
bpy.context.view_layer.update()
# Original V002 defect: parenting shifted the central leaf ~60cm relative to hardware.
# Use the evaluated inverse parent matrix to keep every world transform unchanged.
for ob in objects:
    prev=ob.matrix_world.copy()
    ob.parent=root
    ob.matrix_parent_inverse=root.matrix_world.inverted()
    bpy.context.view_layer.update()
    diff=max(abs(ob.matrix_world[r][c]-prev[r][c]) for r in range(4) for c in range(4))
    assert diff<1e-4,("DOOR_COMPONENT_WORLD_TRANSFORM_DRIFT",ob.name,diff)
    if ob.type=="CURVE":
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.convert(target="MESH")

# V080 correct UVs BEFORE renders: continuous planar projection for the
# custom hammered plate and arched door surfaces. No geometry edits.
# The export uses exactly these UVs; the previous smart unwrap broke the
# hand-forged surface into visually distracting small UV islands.
bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
for ob in root.children:
    if ob.type!="MESH": continue
    ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    if ob.name.startswith("Hand-hammered_twisted_sheet_") or ob.name=="Door_arched_iron_body":
        mesh_data=ob.data
        uv=mesh_data.uv_layers.active or mesh_data.uv_layers.new(name="ContinuousDoorPBR")
        xs=[v.co.x for v in mesh_data.vertices]
        zs=[v.co.z for v in mesh_data.vertices]
        minx,maxx=min(xs),max(xs);minz,maxz=min(zs),max(zs)
        dx=max(maxx-minx,1e-6);dz=max(maxz-minz,1e-6)
        for poly in mesh_data.polygons:
            for li in poly.loop_indices:
                co=mesh_data.vertices[mesh_data.loops[li].vertex_index].co
                uv.data[li].uv=((co.x-minx)/dx,(co.z-minz)/dz)
        continue
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=.015)
    bpy.ops.object.mode_set(mode="OBJECT")

def light(loc,power,size):
    ld=bpy.data.lights.new("studio area","AREA")
    obj=bpy.data.objects.new("studio area",ld)
    bpy.context.collection.objects.link(obj)
    obj.location=loc
    ld.energy=power;ld.shape="DISK";ld.size=size
    obj.rotation_euler=(Vector((0,0,1.15))-obj.location).to_track_quat("-Z","Y").to_euler()
light((-3,-4,4),960,1.8)
light((4.8,1.1,2.9),650,3.2)
light((1,-2,3),230,1.6)
light((0,-3.3,1.35),75,3.0)
light((2.1,-3.1,2.5),410,0.75)
light((-2,4.5,3.2),570,4.0)  # Dedicated rear QA fill reveals anchor connections.
sc=bpy.context.scene
# Genuine neutral studio reflections: black-world rendering concealed metal BRDF behavior.
# CC0 Poly Haven studio_small_09 HDRI is loaded solely for product-preview lighting.
world=bpy.data.worlds.new("V080_StudioHDRI_For_Metal_QA")
world.use_nodes=True
wn=world.node_tree.nodes
wn.clear()
env=wn.new("ShaderNodeTexEnvironment")
env.image=bpy.data.images.load("studio_small_09_1k.hdr")
background=wn.new("ShaderNodeBackground")
background.inputs["Strength"].default_value=.21
output=wn.new("ShaderNodeOutputWorld")
world.node_tree.links.new(env.outputs["Color"],background.inputs["Color"])
world.node_tree.links.new(background.outputs["Background"],output.inputs["Surface"])
sc.world=world
sc.render.engine="CYCLES"
sc.cycles.samples=56
bpy.context.view_layer.cycles.use_denoising=True
sc.render.resolution_x=1080
sc.render.resolution_y=1440
sc.render.resolution_percentage=100
sc.render.film_transparent=True
sc.view_settings.view_transform="AgX"
# V080 visual A/B/C tests: identical approved V011 base mesh + V056 plate tone.
# Remove the colored / glossy ornamental overlay WITHOUT touching the plate shader.
def overlay_finish(m, rgb, metall, rough):
    bs=m.node_tree.nodes.get("Principled BSDF")
    nodes=m.node_tree.nodes; links=m.node_tree.links
    for sock in ("Base Color","Metallic","Roughness"):
        for lk in tuple(bs.inputs[sock].links): links.remove(lk)
    bs.inputs["Base Color"].default_value=(*rgb,1.0)
    bs.inputs["Metallic"].default_value=metall
    bs.inputs["Roughness"].default_value=rough

# V080 — RESTORE PHYSICALLY METALLIC COPPER REFLECTIONS WITH EXACT V071-C COLOR.
# Based on Arcanist V024 multi-scale, COHERENT independent albedo, metallic,
# roughness and normal maps; NOT a global dark photo filter. No glowing effects.
# V068-C remains the approved COLOR DIRECTION (not yet texture approved).
# The original 4K photographed albedo (pink veining, marble-like streaks) is
# explicitly NOT used on B/C material surfaces.
# Keep every V011 geometry vertex and the V068-C ornament materials unchanged.
sc.cycles.samples=48
sc.render.resolution_x=1080
sc.render.resolution_y=1440
hidden_covers=[]
for ob in root.children:
    if ob.name.startswith(("Hand-hammered_twisted_sheet_","Deep_sharp_shadow_inset_")):
        ob.hide_render=True
        hidden_covers.append(ob.name)
assert len(hidden_covers)==6, ("EXPECTED_SIX_COVER_OBJECTS",hidden_covers)
assert all(not ob.hide_render for ob in root.children if ob.name.startswith(("Outer_arch_rolled_rim","Upper_outer_merchant_scroll","Lower_shop_scroll")))
assert door.name=="Door_arched_iron_body"

source=Path("assets/door_herrero/materials/rusted_scratched_iron_4k")
prefix="rusted-scratched-iron_4k_"
maps={}
for channel,suffix in (("albedo","color"),("normal","normalgl"),("metallic","metalness"),("roughness","roughness")):
    path=(source/(prefix+suffix+".jpg")).resolve()
    assert path.is_file(),("SOURCE_MAP_MISSING",str(path))
    img=bpy.data.images.load(str(path),check_existing=True)
    assert tuple(img.size)==(4096,4096),("SOURCE_MAP_NOT_4K",str(path),tuple(img.size))
    if channel!="albedo": img.colorspace_settings.name="Non-Color"
    maps[channel]=img

def dark_brass_pbr(name, brass_color):
    """4K scanned surface relief, with 70% base brass + 30% recolored grayscale
    scan detail. The original scan's WHITE/PINK HUE has ZERO contribution.
    Keeping its luminance variations (not hue) preserves aged metal texture."""
    mat=bpy.data.materials.new("V080_MAIN_LEAF_"+name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    bs=nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*brass_color,1)
    raw=nodes.new("ShaderNodeTexImage")
    raw.label="Imported original 4K albedo — only luminance used"
    raw.image=maps["albedo"]
    grey=nodes.new("ShaderNodeRGBToBW")
    links.new(raw.outputs["Color"],grey.inputs["Color"])
    remap=nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value=0.0
    remap.inputs["From Max"].default_value=1.0
    remap.inputs["To Min"].default_value=.38
    remap.inputs["To Max"].default_value=1.0
    links.new(grey.outputs["Val"],remap.inputs["Value"])
    base=nodes.new("ShaderNodeRGB")
    base.outputs["Color"].default_value=(*brass_color,1)
    colored_scan=nodes.new("ShaderNodeMixRGB")
    colored_scan.blend_type="MULTIPLY"
    colored_scan.inputs[0].default_value=1.0
    links.new(base.outputs["Color"],colored_scan.inputs[1])
    links.new(remap.outputs["Result"],colored_scan.inputs[2])
    combined=nodes.new("ShaderNodeMixRGB")
    combined.blend_type="MIX"
    combined.label="70pct forged brass base / 30pct recolored PBR detail"
    combined.inputs[0].default_value=.30
    links.new(base.outputs["Color"],combined.inputs[1])
    links.new(colored_scan.outputs["Color"],combined.inputs[2])
    links.new(combined.outputs["Color"],bs.inputs["Base Color"])
    # Exactly the same reflective response for all colors, unlike previous
    # tests where changing trim/lighting could obscure the main comparison.
    rough=nodes.new("ShaderNodeTexImage")
    rough.image=maps["roughness"]
    floor=nodes.new("ShaderNodeMath")
    floor.operation="MAXIMUM"
    floor.inputs[1].default_value=.76
    links.new(rough.outputs["Color"],floor.inputs[0])
    links.new(floor.outputs["Value"],bs.inputs["Roughness"])
    metal=nodes.new("ShaderNodeTexImage")
    metal.image=maps["metallic"]
    metallic_scale=nodes.new("ShaderNodeMath")
    metallic_scale.operation="MULTIPLY"
    metallic_scale.inputs[1].default_value=.60
    links.new(metal.outputs["Color"],metallic_scale.inputs[0])
    links.new(metallic_scale.outputs["Value"],bs.inputs["Metallic"])
    ntex=nodes.new("ShaderNodeTexImage")
    ntex.image=maps["normal"]
    normal=nodes.new("ShaderNodeNormalMap")
    normal.space="TANGENT"
    normal.inputs["Strength"].default_value=.65
    links.new(ntex.outputs["Color"],normal.inputs["Color"])
    links.new(normal.outputs["Normal"],bs.inputs["Normal"])
    return mat





# Reproducible PBR bake for the main leaf, 2K review resolution. Independent
# materials, not a stack of alpha overlays. Upgrade to 4K after art approval.
# Models a heat-blackened copper-rich alloy on a physically plausible scale.
N=2048
rng=np.random.default_rng(68291)
def smooth_noise(grid):
    """Smooth 2D random forge/oxidation signal; no diagonal scanned streaks."""
    a=np.linspace(0,grid-1,N,dtype=np.float32)
    ix=np.floor(a).astype(np.int32)
    t=a-ix;t=t*t*(3-2*t)
    nx=np.minimum(ix+1,grid-1)
    vals=rng.standard_normal((grid,grid)).astype(np.float32)
    # grid indices: (vertical, horizontal), deterministic for each call.
    t1=t[:,None];t2=t[None,:]
    return (
        vals[ix[:,None],ix[None,:]]*(1-t1)*(1-t2)
       +vals[nx[:,None],ix[None,:]]*t1*(1-t2)
       +vals[ix[:,None],nx[None,:]]*(1-t1)*t2
       +vals[nx[:,None],nx[None,:]]*t1*t2
    ).astype(np.float32)

macro=smooth_noise(8)
broad=smooth_noise(37)
fine=smooth_noise(173)
pore=smooth_noise(597)
micro=rng.standard_normal((N,N)).astype(np.float32)
sat=lambda v:np.clip(v,0.0,1.0)

# Low-frequency VARIATION affects oxidation and roughness, NOT giant patchy
# albedo stripes or washed-out pink islands. Small local oxidation islands:
oxide=sat((.36*macro+.34*broad+.14*fine-.10)*1.38)
oxide=np.power(oxide,1.18).astype(np.float32)
soot=sat((.35*macro+.24*broad-.24)*1.24)
freckles=sat((.55*pore+.20*fine+.12*micro-.25)*1.5)
# Actual pits are localized shallow circular hammer strikes, never hairlines.
bump=(.50+.008*macro+.017*broad+.027*fine+.025*pore+.009*micro).astype(np.float32)
dent_rng=np.random.default_rng(26745)
for k in range(1320):
    x=int(dent_rng.integers(20,N-20))
    y=int(dent_rng.integers(20,N-20))
    radius=int(dent_rng.integers(8,23))
    stretch=float(dent_rng.uniform(.72,1.32))
    iy0=max(0,y-2*radius);iy1=min(N,y+2*radius+1)
    ix0=max(0,x-2*radius);ix1=min(N,x+2*radius+1)
    yy,xx=np.ogrid[iy0:iy1,ix0:ix1]
    rr=((xx-x)/(radius*stretch))**2+((yy-y)/radius)**2
    # depressed bowl, soft shoulder; no raised sharp doodles.
    dent= -.063*np.exp(-rr*1.80)+.014*np.exp(-((rr-1.0)**2)*2.7)
    bump[iy0:iy1,ix0:ix1]+=dent.astype(np.float32)
del micro

# Metal is exposed on broad body, oxidation only in localized zones.
# Match metallic response and roughness to physically CORRELATED corrosion.
metallicmap=np.clip(.86-.68*oxide-.36*soot+.018*fine,.11,.93).astype(np.float32)
roughmap=np.clip(.58+.22*oxide+.13*soot+.044*fine+.024*pore,.52,.94).astype(np.float32)
# Facets are *normal map* changes, not distracting drawn scars or pink strokes.
gx=np.gradient(bump,axis=1)*6.3
gy=np.gradient(bump,axis=0)*6.3
norm=np.sqrt(gx*gx+gy*gy+1)
normal=np.stack((.5-.5*gx/norm,.5-.5*gy/norm,.5+.5/norm),axis=-1).astype(np.float32)
del gx,gy,norm,bump
# Wear on tiny exposed high points only (no uniform luminous edge strip).
micro_wear=sat((.16+.25*fine+.12*pore-.42*oxide-.17*soot)*1.60).astype(np.float32)
# Deliberately small albedo variation; no photographic color or scanned veining.
grain=np.clip(1+.050*broad+.034*fine+.014*pore,.86,1.14).astype(np.float32)
del macro,broad,fine,pore

def baked_map(tag,rgb,noncolor=True):
    """Write actual PNG, packed and assigned to glTF-compatible image node."""
    if rgb.ndim==2:
        rgb=np.repeat(rgb[:,:,None],3,axis=2)
    rgba=np.empty((N,N,4),dtype=np.float32)
    # Bitmap PNG Base Color is encoded in sRGB, while the procedural copper
    # palette above is LINEAR. Explicit encoding avoids ultra-dark albedo bytes
    # that previously caused neutral HDRI reflections to overpower copper.
    if not noncolor:
        linear=np.clip(rgb,0.0,1.0)
        encoded=np.where(linear<=.0031308,12.92*linear,
                         1.055*np.power(linear,1/2.4)-.055)
        rgb=encoded.astype(np.float32)
    rgba[:,:,:3]=np.clip(rgb,0,1)
    rgba[:,:,3]=1.0
    im=bpy.data.images.new("V080_"+tag,width=N,height=N,alpha=True)
    if noncolor: im.colorspace_settings.name="Non-Color"
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw=str(OUT/("V080_"+tag+".png"))
    im.file_format="PNG"
    im.save()
    im.pack()
    print("V080_PBR_BAKE",tag,im.size[:],flush=True)
    del rgba
    return im

pbr_rough=baked_map("roughness",roughmap)
pbr_metal=baked_map("metalness",metallicmap)
pbr_normal=baked_map("normal_opengl",normal)
del metallicmap,roughmap,normal

# Genuine spatial patina: metal color remains warm blackened COPPER.
# Wear and oxide follow the same height/roughness/metallic phenomenon.
def make_copper_albedo(name,metal_rgb,oxide_rgb,soot_strength):
    base=np.asarray(metal_rgb,dtype=np.float32)
    rust=np.asarray(oxide_rgb,dtype=np.float32)
    # Subtle forging differences; oxide has NO blue/green patina and is NOT white.
    color=base[None,None,:]*grain[:,:,None]
    rust_amount=np.clip(oxide*(.58+.13*freckles),0,.69)[:,:,None]
    color=color*(1-rust_amount)+rust[None,None,:]*rust_amount
    color*=np.clip(1-soot_strength*soot[:,:,None],.55,1)
    exposed=np.asarray((.102,.043,.022),dtype=np.float32)
    wear_weight=(.23*micro_wear)[:,:,None]
    color=color*(1-wear_weight)+exposed[None,None,:]*wear_weight
    return baked_map(name+"_albedo",color,False)

B_COLOR=(.033,.013,.008)
C_COLOR=(.024,.009,.006)
b_col=make_copper_albedo("B_forged_oxidized_copper",B_COLOR,(.013,.011,.010),.62)
c_col=make_copper_albedo("C_heat_blackened_copper",C_COLOR,(.010,.009,.008),.80)
del grain,micro_wear,oxide,soot,freckles

def new_forged_copper_mat(name,albedo):
    mat=bpy.data.materials.new("V080_Copper_RealPBR_"+name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    bs=nodes.get("Principled BSDF")
    for image,socket in ((albedo,"Base Color"),(pbr_rough,"Roughness"),
                         (pbr_metal,"Metallic")):
        node=nodes.new("ShaderNodeTexImage")
        node.image=image;node.interpolation="Linear"
        node.label="V080 baked measured-role PBR: "+socket
        links.new(node.outputs["Color"],bs.inputs[socket])
    nl=nodes.new("ShaderNodeTexImage")
    nl.image=pbr_normal;nl.interpolation="Linear"
    tangent=nodes.new("ShaderNodeNormalMap")
    tangent.space="TANGENT"
    tangent.inputs["Strength"].default_value=.92
    links.new(nl.outputs["Color"],tangent.inputs["Color"])
    links.new(tangent.outputs["Normal"],bs.inputs["Normal"])
    assert all(bs.inputs[k].is_linked for k in ("Base Color","Roughness","Metallic","Normal"))
    return mat

# Exact V068-C reference, kept in this new workflow for an honest side-by-side.
mat=dark_brass_pbr("A_v068C_reference",(.145,.037,.020))
nodes=mat.node_tree.nodes;links=mat.node_tree.links
bs=nodes.get("Principled BSDF")
old_link=list(bs.inputs["Base Color"].links)
assert len(old_link)==1
old_socket=old_link[0].from_socket
links.remove(old_link[0])
overlay=nodes.new("ShaderNodeMixRGB")
overlay.blend_type="MIX";overlay.inputs[0].default_value=.70
overlay.inputs[2].default_value=(.018,.006,.004,1.0)
links.new(old_socket,overlay.inputs[1])
dark=nodes.new("ShaderNodeMixRGB")
dark.blend_type="MULTIPLY";dark.inputs[0].default_value=1.
dark.inputs[2].default_value=(.26,.26,.26,1.0)
links.new(overlay.outputs["Color"],dark.inputs[1])
links.new(dark.outputs["Color"],bs.inputs["Base Color"])

# V080: isolate only the reflection response on the exact V071-C forged
# copper texture. Albedo, tangent normal, all original pixels, UV and
# ornamental objects/materials are byte-for-byte the same in each image.
def tuned_leaf_mat(name, metal_scale=1.0, rough_floor=None):
    m=new_forged_copper_mat(name,c_col)
    bs=m.node_tree.nodes.get("Principled BSDF")
    nodes=m.node_tree.nodes
    links=m.node_tree.links
    if metal_scale!=1.0:
        current=list(bs.inputs["Metallic"].links)
        assert len(current)==1
        old=current[0].from_socket
        links.remove(current[0])
        mult=nodes.new("ShaderNodeMath")
        mult.operation="MULTIPLY"
        mult.inputs[1].default_value=metal_scale
        mult.label="V080 retain metalness map but temper overbright steel-gray reflection"
        links.new(old,mult.inputs[0])
        links.new(mult.outputs[0],bs.inputs["Metallic"])
    if rough_floor is not None:
        current=list(bs.inputs["Roughness"].links)
        assert len(current)==1
        old=current[0].from_socket
        links.remove(current[0])
        floor=nodes.new("ShaderNodeMath")
        floor.operation="MAXIMUM"
        floor.inputs[1].default_value=rough_floor
        floor.label="V080 physical soot/oxidation satin finish"
        links.new(old,floor.inputs[0])
        links.new(floor.outputs[0],bs.inputs["Roughness"])
    assert all(bs.inputs[k].is_linked for k in ("Base Color","Roughness","Metallic","Normal"))
    return m

# V080: MATERIAL-ONLY ART EXPERIMENT against actual inspected V077 renders.
# V077 revealed grey marble-like plate reflections and circular dents.
# V080 preserves V011 mesh, V068-C ornaments and studio lighting, suppresses
# macro patina, concentrates non-metallic black scale and isolates true exposed
# iron wear to shallow hammered crests. Do not promote until 4-view inspection.
# V080 — BLACK FORGED IRON WITH RESTRAINED ALBEDO AND NON-CLOUDY HAMMER WEAR
# Previous V073-B was archived to production/door-curtidor-v073-rescue:
# its pebbled, diffuse copper happened to resemble leather, NOT forged iron.
# The geometry, ornaments and studio lights are unchanged. Only the flat door
# leaf gets new PBR textures here. Material is based on REAL oxidized iron:
# exposed metallic iron at hammer shoulders / edges, nonmetal soot/oxide in
# recesses and irregular patches. Never use photo-printed albedo streaks.
# Keep V073-B exactly as control A, render two iron variations and B closeup.
# 2K exploratory PBR — 4K master and optimized GLB after approval.

RES=2048
mt_rng=np.random.default_rng(74740)
def forge_noise(grid):
    a=np.linspace(0,grid-1,RES,dtype=np.float32)
    i=np.floor(a).astype(np.int32)
    t=a-i;t=t*t*(3-2*t)
    j=np.minimum(i+1,grid-1)
    randoms=mt_rng.standard_normal((grid,grid)).astype(np.float32)
    v0=randoms[i[:,None],i[None,:]]
    v1=randoms[j[:,None],i[None,:]]
    v2=randoms[i[:,None],j[None,:]]
    v3=randoms[j[:,None],j[None,:]]
    ty=t[:,None];tx=t[None,:]
    return (v0*(1-ty)*(1-tx)+v1*ty*(1-tx)+v2*(1-ty)*tx+v3*ty*tx).astype(np.float32)

def saturate(a):
    return np.clip(a,0.0,1.0)
m=forge_noise(12)
broad=forge_noise(52)
fine=forge_noise(218)
micro=forge_noise(520)
# All impacts are shallow elliptic hammer depressions with an irregular
# shoulder. No uniform rough pebbles, no long thin scratches ("rayitas").
height=(.5+.004*m+.005*broad+.011*fine+.003*micro).astype(np.float32)
impact=np.zeros((RES,RES),dtype=np.float32)
dent_rng=np.random.default_rng(180574)
for i in range(350):
    cx=int(dent_rng.integers(37,RES-37)); cy=int(dent_rng.integers(37,RES-37))
    rad=int(dent_rng.integers(13,30))
    sx=float(dent_rng.uniform(.75,1.35))
    y0=max(0,cy-2*rad);y1=min(RES,cy+2*rad+1)
    x0=max(0,cx-2*rad);x1=min(RES,cx+2*rad+1)
    yy,xx=np.ogrid[y0:y1,x0:x1]
    rr=((xx-cx)/(rad*sx))**2+((yy-cy)/rad)**2
    dent=(-.040*np.exp(-rr*1.80)+.009*np.exp(-((rr-1.08)**2)*2.5)).astype(np.float32)
    impact[y0:y1,x0:x1]+=dent
height+=impact
del impact
dx=np.gradient(height,axis=1)*8.0
dy=np.gradient(height,axis=0)*8.0
norm=np.sqrt(dx*dx+dy*dy+1)
normal=np.stack((.5-.5*dx/norm,.5-.5*dy/norm,.5+.5/norm),axis=-1).astype(np.float32)
hammer_rim=saturate((np.sqrt(dx*dx+dy*dy)-.006)*12.0).astype(np.float32)
del height,dx,dy,norm

# Scale and oxidation are nonmetallic. Exposed forged iron beneath has
# genuinely high metallic response. PBR masks correlate to the same scale.
# Oxide has a stable black forged body with ONLY restrained local fluctuations;
# prior ±0.31 macro noise created marble/cloud-like diffuse patches.
scale=saturate(.955+.014*m+.008*broad+.005*fine)
fine_corrosion=saturate(.32+.27*fine+.24*micro-.10)
u=np.linspace(0,1,RES,dtype=np.float32)
uu=u[None,:]; vv=u[:,None]
edge=saturate(np.exp(-uu/.017)+np.exp(-(1-uu)/.017)
              +np.exp(-vv/.029)+np.exp(-(1-vv)/.029))
# Less oxide on worked crests/edges; oxidized recesses and hammer footings.
oxide=saturate(scale*(.99+.014*fine_corrosion)-.11*edge-.070*hammer_rim)
# Iron abrasion is highly local and does not make the full face bright grey.
wear=saturate(.05+.035*broad+.03*fine+.21*edge-.33*oxide+.26*hammer_rim)
del m,broad,scale

def encode_srgb(rgb):
    values=np.clip(rgb,0.0,1.0)
    return np.where(values<=.0031308,12.92*values,
                    1.055*np.power(values,1/2.4)-.055).astype(np.float32)

def save_forge_map(name, rgb, noncolor):
    if rgb.ndim==2:
        rgb=np.repeat(rgb[:,:,None],3,axis=2)
    if not noncolor:
        rgb=encode_srgb(rgb)
    im=bpy.data.images.new("V080_"+name,width=RES,height=RES,alpha=True)
    if noncolor:im.colorspace_settings.name="Non-Color"
    rgba=np.empty((RES,RES,4),dtype=np.float32)
    rgba[:,:,:3]=np.clip(rgb,0,1)
    rgba[:,:,3]=1
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw=str(OUT/("V080_"+name+".png"))
    im.file_format="PNG"
    im.save();im.pack()
    print("V080_PBR_SAVED",name,flush=True)
    del rgba
    return im

def build_metal_maps(name, exposed_color, oxide_color, oxidation, warm_rust, roughness_gain=0.0, micro_gain=0.0, metal_gain=0.0):
    # Metalness high only on truly exposed metal; chemically oxidized material
    # is rough + low metalness and looks like genuine black forge scale.
    ox=saturate(oxide*oxidation)
    # Avoid neutral highlight the size of the entire door: most surface scale.
    metalness=np.clip(.92-.90*ox+.18*wear+metal_gain*(1-.35*ox),.015,.94).astype(np.float32)
    rough=np.clip(.77+.17*ox+.014*fine+.009*micro-.15*wear+roughness_gain+micro_gain*(.55*fine+.34*micro),.55,.98).astype(np.float32)
    # With correlated hue, oxide recesses are dark matte; visible metal shows
    # warm alloy or cool steel hue. Orange rust only very sparse micro islands.
    bare=np.array(exposed_color,dtype=np.float32)
    black=np.array(oxide_color,dtype=np.float32)
    exposed_bump=np.clip(1+.027*fine+.015*micro,.93,1.07).astype(np.float32)
    col=(bare[None,None,:]*exposed_bump[:,:,None]*(1-ox[:,:,None])
          +black[None,None,:]*ox[:,:,None])
    color_wear=np.array((.145,.148,.142),dtype=np.float32)
    col=col*(1-(.12*wear)[:,:,None])+color_wear[None,None,:]*(.12*wear)[:,:,None]
    if warm_rust>0:
        rust=saturate((fine_corrosion-.43)*2.5)*(ox**1.7)*warm_rust
        reddish=np.array((.085,.036,.020),dtype=np.float32)
        col=col*(1-rust[:,:,None])+reddish[None,None,:]*rust[:,:,None]
    color_img=save_forge_map(name+"_albedo",col,False)
    metal_img=save_forge_map(name+"_metalness",metalness,True)
    rough_img=save_forge_map(name+"_roughness",rough,True)
    del metalness,rough,col
    return color_img,metal_img,rough_img

n_img=save_forge_map("normal_opengl",normal,True)
del normal
B_COLOR=(.145,.149,.148)   # bare neutral forged iron: physically metallic
B_SCALE=(.0035,.0045,.0050)   # hot black scale; never white gray
C_COLOR=(.137,.119,.100)   # warmer temper/hammer steel with brown undertone
C_SCALE=(.0060,.0050,.0040)   # black-brown forge scale, less blue
# Both V080 variants reuse EXACT V080 warm-blackened color, oxidation and geometry.
# Only metalness, roughness (including irregular microvariance), and normal strength vary.
b_maps=build_metal_maps("A_approved_color_medium",C_COLOR,C_SCALE,1.02,.17,
                       roughness_gain=.017,micro_gain=.023,metal_gain=.12)
c_maps=build_metal_maps("B_approved_color_textured",C_COLOR,C_SCALE,1.02,.17,
                       roughness_gain=.032,micro_gain=.045,metal_gain=.20)
del oxide,wear,fine,micro,fine_corrosion,edge,hammer_rim

def real_iron_material(name,image_triplet,normal_strength=.90):
    color,metal,rough=image_triplet
    mat=bpy.data.materials.new("V080_TrueForgedIron_"+name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    bs=nodes.get("Principled BSDF")
    for image,slot in ((color,"Base Color"),(metal,"Metallic"),(rough,"Roughness")):
        t=nodes.new("ShaderNodeTexImage")
        t.image=image
        links.new(t.outputs["Color"],bs.inputs[slot])
    tex=nodes.new("ShaderNodeTexImage")
    tex.image=n_img
    nm=nodes.new("ShaderNodeNormalMap")
    nm.space="TANGENT";nm.inputs["Strength"].default_value=normal_strength
    links.new(tex.outputs["Color"],nm.inputs["Color"])
    links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    assert all(bs.inputs[k].is_linked for k in ("Base Color","Metallic","Roughness","Normal"))
    return mat

# V080 — Surface realism correction with NON-CLOUDY black forge scale.
# Historical wrought iron can have a relatively smooth, dark oxide skin and
# small irregular hammer marks. The prior V075/V076 broad noise looked marble.
# All hardware materials and V011 mesh remain untouched. Product lighting
# fixed at 40% for A/B, with darker 25% C as controlled extra comparison.
metal_b=real_iron_material("A_medium",b_maps,normal_strength=1.06)
metal_c=real_iron_material("B_textured",c_maps,normal_strength=1.22)
all_studio_lights=[o for o in bpy.data.objects if o.type=="LIGHT" and o.data.type=="AREA"]
assert len(all_studio_lights)==6,("STUDIO_LIGHT_COUNT",len(all_studio_lights))
original_powers={o.name:float(o.data.energy) for o in all_studio_lights}
original_hdri=float(background.inputs["Strength"].default_value)
assert abs(original_hdri-.21)<1e-4

def set_review_lighting(power_factor):
    for lamp in all_studio_lights:
        lamp.data.energy=original_powers[lamp.name]*power_factor
    background.inputs["Strength"].default_value=.14
    print("V080_STUDIO_POWER",power_factor,"HDRI .14",flush=True)

def render_metal(name,mat):
    door.data.materials.clear()
    door.data.materials.append(mat)
    bpy.ops.object.camera_add(location=(2.3,-5,1.7))
    camera=bpy.context.object
    camera.rotation_euler=(Vector((0,0,1.15))-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type="ORTHO"
    camera.data.ortho_scale=2.53
    sc.camera=camera
    sc.render.resolution_x=1080;sc.render.resolution_y=1440
    sc.render.filepath=str(OUT/(name+".png"))
    bpy.ops.render.render(write_still=True)
    assert (OUT/(name+".png")).stat().st_size>1024,name
    print("V080_METAL_RENDERED",name,flush=True)

# Fixed illumination and camera across both material experiments; V080 color unchanged.
set_review_lighting(.40)
render_metal("A_V080_medium_roughness_metalness",metal_b)
render_metal("B_V080_stronger_roughness_metalness",metal_c)
def render_closeup(name, mat):
    door.data.materials.clear()
    door.data.materials.append(mat)
    bpy.ops.object.camera_add(location=(.9,-3.3,1.08))
    cam=bpy.context.object
    cam.rotation_euler=(Vector((0,0,1.04))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=1.04
    sc.camera=cam;sc.render.resolution_x=1080;sc.render.resolution_y=1080
    sc.render.filepath=str(OUT/(name+".png"))
    bpy.ops.render.render(write_still=True)
    assert (OUT/(name+".png")).stat().st_size>1024
render_closeup("C_V080_medium_surface_detail",metal_b)
render_closeup("D_V080_stronger_surface_detail",metal_c)
for lamp in all_studio_lights: lamp.data.energy=original_powers[lamp.name]
background.inputs["Strength"].default_value=original_hdri
# The production-approved COLOR is exactly equal in both V080 shader candidates.
import hashlib
map_a=OUT/"V080_A_approved_color_medium_albedo.png"
map_b=OUT/"V080_B_approved_color_textured_albedo.png"
hash_a=hashlib.sha256(map_a.read_bytes()).hexdigest()
hash_b=hashlib.sha256(map_b.read_bytes()).hexdigest()
assert hash_a==hash_b, "CRITICAL: approved V080 color has drifted between V080 variants"
with (OUT/"V080_USER_COLOR_PRESERVATION_QA.json").open("w",encoding="utf-8") as f:
    json.dump({
      "version":"V080", "approved_reference":"V079 warm-blackened color",
      "artist_instruction":"Preserve V079 color; increase genuine fine surface roughness and a little metallic response",
      "V079_geometry_unchanged":True, "ornaments_unchanged":True,
      "moderate":{"roughness_gain":.017,"micro_gain":.023,"metal_gain":.12,"normal_strength":1.06},
      "stronger":{"roughness_gain":.032,"micro_gain":.045,"metal_gain":.20,"normal_strength":1.22},
      "albedo_sha256":hash_a, "variant_albedos_identical":hash_a==hash_b,
      "studio_power":.40,"HDRI_strength":.14,
      "user_approval":"V079 nearly functional with color approved; V080 surface subject to visual validation",
      "GLB_generated":False, "PlayCanvas_validated":False
    },f,indent=2)
with (OUT/"V080_VISUAL_QA.json").open("w",encoding="utf-8") as f:
    json.dump({
      "version":"V080",
      "goal":"Eliminate rock/marble clouds from forged iron, reveal metal/hammered plate",
      "old_materials_reference":"V075/V076",
      "studio_power_A_B":.40,"studio_power_C":.25,"HDRI":.14,
      "geometry":"V011 unchanged","ornament_graphs_modified":False,
      "new_maps":"2K diffuse albedo, metallic, roughness and normal, black forge oxide",
      "hammer_rim_correlated":True,
      "removed_macro_clouds":True,
      "approval":"PENDING_VISUAL_AND_PLAYCANVAS",
      "glb_generated":False
    },f,indent=2)

with (OUT/"V080_METAL_VS_LEATHER_QA.json").open("w",encoding="utf-8") as f:
    json.dump({
      "version":"V080","status":"PENDING_USER_VISUAL_APPROVAL",
      "archived_curtidor_branch":"production/door-curtidor-v073-rescue",
      "archived_reference":"V073-B B_full_metal_copper.png",
      "new_goal":"diagnose V075 appearance under softer studio with identical material PBR maps",
      "why_prior_failed":"V073 was leatherlike; V074 oxide too thin, studio overexposed silver panel",
      "reference_geometry":"V011 unchanged",
      "only_changed_object":"Door_arched_iron_body",
      "ornaments":"V073 unchanged, no graph modifications",
      "photographic_scan_in_new_iron":False,
      "albedo_encoding":"linear to sRGB encoded PNG",
      "PBR_source":"procedural reproducible independent 2K maps",
      "maps":["normal_opengl","B_blackened_forged_iron_albedo",
              "B_blackened_forged_iron_metalness","B_blackened_forged_iron_roughness",
              "C_warm_tempered_forged_iron_albedo",
              "C_warm_tempered_forged_iron_metalness","C_warm_tempered_forged_iron_roughness"],
      "hammering":"510 irregular wide shallow indentations, no hairline etches",
      "same_lighting":True,"same_ornaments":True,
      "geometry_exported_as_glb":False,
      "webgl_optimization":"not validated"
    },f,indent=2)

with (OUT/"V080_PBR_QA.json").open("w",encoding="utf-8") as f:
    json.dump({
        "version":"V080","reference":"V071-C visual realism ~7.8; V072 lower metalness became grey",
        "method":"V071-C coherent PBR and identical color/normal; raise metallic toward 1 while retaining oxide areas",
        "approved_geometry":"V011 untouched",
        "ornament_materials":"V068-C unchanged",
        "source_4K_albedo_on_B_or_C":False,
        "why":"photo contained unrealistic pale pink streaks/huge patches",
        "explicit_baked_maps":["V080_roughness.png","V080_metalness.png",
          "V080_normal_opengl.png","V080_B_forged_oxidized_copper_albedo.png",
          "V080_C_heat_blackened_copper_albedo.png"],
        "baked_texture_resolution":2048,
        "surface_wear":"only from local oxidation/pitting/raised wear mask",
        "removed_cover_sheets_and_underlays":hidden_covers,
        "ornaments_and_hardware_untouched":True,
        "physical_roughness_ranges":[.52,.94],
        "physical_metallic_ranges":[.11,.93],
        "no_hairline_geometry":True,
        "status":"VISUAL_REVIEW_REQUIRED","target_realism":8.0
    },f,indent=2)

# Evaluated triangles include bevels and converted ornamental curves.
dg=bpy.context.evaluated_depsgraph_get()
triangles=0
for ob in root.children:
    if ob.type!="MESH": continue
    ev=ob.evaluated_get(dg)
    me=ev.to_mesh()
    triangles+=len(me.loop_triangles)
    ev.to_mesh_clear()
print("DOOR_V011_EVALUATED_TRIANGLES",triangles,flush=True)
with (OUT/"DESIGN_AUDIT.json").open("w") as f:
    json.dump({"source":"V080 new 2K baked coherent forged-copper material on V011 main leaf; ornaments unchanged",
        "version":"V080","baseline_version":"V010",
        "targeted_repairs":["preserve connected rear structural braces and peephole through-mesh",
                            "reduce tiny rivet cylinders and curve tessellation below silhouette threshold",
                            "reduce hidden hammer plate subdivisions without removing PBR relief",
                            "reduce bevel segments and retain edge catchlights for front and side views"],
        "legacy_meshes_reused":0,"shape":"arched_iron_merchant_shop",
        "true_circular_peep_hole":True,"lever_count":1,"wood":False,
        "texture_pixels":4096,"texture_max_allowed":4096,
        "geometry_budget_target_triangles":25000,"evaluated_triangles":triangles,
        "budget_met":triangles<=25000,
        "note":"Budget is a target, not an automatic art approval; compare silhouette in four views"},f,indent=2)

with (OUT/"V080_MATERIAL_TEST.json").open("w",encoding="utf-8") as f:
    json.dump({"version":"V080","geometry_baseline":"V011_USER_APPROVED",
      "material_goal":"V080 rebuilt copper/oxide PBR separate maps with correlation between base-color/metallic/roughness/normal; preserve geometry",
      "source_texture_copied":True,
      "exact_V175_material_applied":False,
      "additional_photo_scan":"Meshy / ambientCG CC0 rusted-scratched-iron original 4K",
      "reason":"Original complete CC0 scan applied to plate without modifying its channels",
      "material_only":True,"artist_approval":"PENDING"},f,indent=2)

# V080 provenance: actual V077 four-view inspection 2026-11-01.
# This is a review-only material candidate; no game import or art approval.
