# Door V011: real rear hinge-side reinforcement connections and legible metal QA.
# Blender 4.5 / PlayCanvas GLB; all scene generation runs in GitHub Actions.
import bpy, math, json, random, os
from math import sin, cos, pi
from pathlib import Path
from mathutils import Vector
import numpy as np

TRADE=os.environ.get("PG_DOOR_TRADE","carpintero").strip().lower()
assert TRADE in ("herrero","carpintero","curtidor","joyero","arcanista"),TRADE
OUT=Path("output_workshop_door_v022_"+TRADE)
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
random.seed(26)
# V011 silhouette is artist-approved; only physical PBR surfaces vary by profession.

# Dimensions reference hero: width 1.2 m, max height 2.31 m, 0.104 m thick.
WIDTH=1.20
BASE=.035
SPRING=1.775
RISE=.525
FRONT=-.057
BACK=.057
CENTER_PEEP=1.52
HANDLE_Z=1.035

# Palette: leaf panel, raised ironwork, handle metal, and recessed insets.
# Surface materials use their own roughness, metallic, normal and albedo channels.
# This is intentionally four material roles over exactly the approved V011 geometry.
PROFILES={
    "herrero":{"leaf":((.125,.130,.141),.93,.50,"iron"),
               "edge":((.104,.108,.112),.89,.67,"iron"),
               "hardware":((.185,.117,.076),.81,.59,"bronze"),
               "inset":((.112,.116,.119),.87,.74,"iron")},
    "carpintero":{
        "leaf":((.31,.187,.092),.0,.72,"oak"),
        "edge":((.124,.137,.143),.87,.60,"iron"),
        "hardware":((.316,.235,.134),.84,.55,"bronze"),
        "inset":((.145,.087,.041),.0,.83,"oak"),
    },
    "curtidor":{
        "leaf":((.145,.080,.048),.0,.82,"oak"),
        "edge":((.110,.119,.120),.87,.69,"iron"),
        "hardware":((.278,.239,.174),.78,.61,"bronze"),
        "inset":((.245,.113,.061),.0,.83,"leather"),
    },
    "joyero":{
        "leaf":((.114,.125,.130),.92,.44,"iron"),
        "edge":((.405,.277,.126),.85,.40,"bronze"),
        "hardware":((.492,.337,.143),.89,.36,"bronze"),
        "inset":((.177,.119,.072),.74,.60,"bronze"),
    },
    "arcanista":{
        "leaf":((.013,.030,.089),.0,.60,"arcane_lithic"),
        "edge":((.023,.051,.081),.0,.54,"arcane_lithic"),
        "hardware":((.055,.083,.121),.04,.47,"arcane_lithic"),
        "inset":((.010,.022,.072),.0,.65,"arcane_lithic"),
    },
}
def material(name, base, metallic, roughness, seed, surface):
    """Distinct spatially non-uniform basecolor/metallic/roughness/normal (+ arcane emission).
    All PBR maps baked into glTF-compatible image nodes. No simple color recoloring."""
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*base,1)
    bs=m.node_tree.nodes.get("Principled BSDF")
    n=int(os.environ.get("PG_PBR_RES","2048"))
    assert n in (1536,2048,4096)
    rng=np.random.default_rng(seed)
    def sn(grid):
        ax=np.linspace(0,grid-1,n,dtype=np.float32)
        ix=np.floor(ax).astype(np.int32);t=ax-ix
        t=t*t*(3.-2*t);jx=np.minimum(ix+1,grid-1)
        val=rng.standard_normal((grid,grid)).astype(np.float32)
        return (val[ix[:,None],ix[None,:]]*(1-t[:,None])*(1-t[None,:])
             +val[jx[:,None],ix[None,:]]*t[:,None]*(1-t[None,:])
             +val[ix[:,None],jx[None,:]]*(1-t[:,None])*t[None,:]
             +val[jx[:,None],jx[None,:]]*t[:,None]*t[None,:])
    macro=sn(9);broad=sn(27);fine=sn(93);pore=sn(223)
    micro=rng.standard_normal((n,n)).astype(np.float32)
    x=np.linspace(0,1,n,dtype=np.float32)[:,None]
    y=np.linspace(0,1,n,dtype=np.float32)[None,:]
    def sat(v):return np.clip(v,0.,1.)
    def mix(a,b,w):return a*(1-w)+b*w
    oxide=None
    emission=None
    if surface=="oak":
        warp=1.25*macro+.57*broad+.18*fine
        # Slightly warped longitudinal fibres, less repetitive than stylized sine stripes.
        grain=.5+.5*np.sin((46*x+warp*3.1)*2*np.pi)
        small=.5+.5*np.sin((110*x+warp*6.7)*2*np.pi)
        # Knots are localized warped elliptical rings (not full-length uniform bands).
        knot_r=np.sqrt(((x-.34)*3.7)**2+((y-.47)*1.9)**2)
        knot=sat(1-abs(knot_r-.37)*7.)*(.5+.5*np.sin(58*knot_r))
        weather=sat(.50+.26*macro+.22*broad+.09*fine)
        streak=.52+.18*grain+.065*small-.08*knot
        modulation=sat(weather*streak+.12)*1.65
        rough=sat(roughness+.085*broad+.035*fine+.028*micro+.12*knot)
        rough=np.clip(rough,.53,.96)
        metallicmap=np.zeros((n,n),dtype=np.float32)
        bump=.50+.062*grain+.034*small+.10*knot+.047*fine+.026*pore
        colored=[.98,.90,.80]
    elif surface=="leather":
        # High-frequency pebbled grain, natural wrinkles and dye absorption pores.
        cell=sat(.45+.60*pore+.24*fine)
        dents=sat((micro-.46)*.28)
        folded=sat(.49+.31*macro+.23*broad)
        weather=sat(.73+.21*macro+.13*broad-.20*dents)
        modulation=np.clip(weather+.17*cell,.43,1.20)
        rough=np.clip(roughness+.10*broad+.035*fine+.065*dents,.64,.98)
        metallicmap=np.zeros((n,n),dtype=np.float32)
        bump=.48+.13*cell+.035*folded-.13*dents+.035*fine
        colored=[1.0,.91,.83]
    elif surface=="arcane_lithic":
        # V024: translucent-seeming, metamorphic arcane stone with sub-surface
        # blue inclusions. It is deliberately NON-METALLIC, never blue iron.
        strata=.55*macro+.30*broad+.15*fine
        cleavage=np.sin((x*8.3+y*3.7+strata*.85)*2*np.pi)
        cleavage2=np.sin((x*17.1-y*9.4+strata*1.3)*2*np.pi)
        sheets=sat(.50+.34*cleavage+.20*cleavage2+.42*strata)
        pores=sat(.48+.29*pore+.18*fine)
        inclusion=sat((.58*macro+.34*broad+.15*fine+.08))
        # Sparse seams from large-scale mineral pressure, NOT repeating wave
        # fields or decorative neon loops. A few deep luminous inclusions only.
        veinfield=.70*macro+.23*broad+.07*fine
        core=np.exp(-((veinfield-.27)/.045)**2)*sat(.54+.35*macro)
        branch=np.exp(-((veinfield+.42)/.033)**2)*.25
        halo=np.exp(-((veinfield-.27)/.18)**2)*.13
        glow=sat((core+branch+halo)*sat(.38+.45*inclusion))
        modulation=np.clip(.44+.38*sheets+.24*strata+.13*pores,.24,1.10)
        rough=np.clip(roughness+.11*pores+.10*fine-.07*inclusion-.07*glow,.49,.96)
        metallicmap=np.full((n,n),metallic,dtype=np.float32)
        bump=.47+.11*sheets+.04*cleavage2+.06*pores+.09*fine-.07*core
        colored=[.55,.81,1.42]
        # Material body is dark blue-violet mineral, cyan from internal fractures.
        color=np.stack([sat(base[k]*modulation*colored[k]) for k in range(3)],axis=-1)
        color += np.stack((.003*inclusion+.008*glow,.013*inclusion+.058*glow,.060*inclusion+.16*glow),axis=-1)
        color=np.clip(color,0,1)
        emission=np.stack((.013*glow,.52*glow,.83*glow),axis=-1)
        print("V024_LITHIC_GLOW",name,float(glow.mean()),float((glow>.4).mean()),flush=True)
    else:
        # Metallurgy: two oxide scales, micro-pitting, impact abrasion and patches
        # of intact forge-polished metal. Metallic and roughness follow the corrosion.
        freckles=sat((micro-.10)*.37+.29*pore)
        oxide=sat((.54*macro+.46*broad+.20*fine-.04)*1.40+.14*freckles)
        oxide=oxide**1.18
        caverns=sat((.45*macro+.42*broad+.32*fine+.12*pore-.22)*2.5)
        scratches=sat((.20*fine+.10*pore+.05*micro))
        wear=sat(.54+.24*broad-.24*oxide+.12*micro)
        if surface=="bronze":
            oxide_color=np.array([.075,.190,.135],dtype=np.float32)
            ox_strength=.45
            rough_inc=.34
        elif surface=="arcane_iron":
            oxide_color=np.array([.035,.100,.164],dtype=np.float32)
            ox_strength=.72
            rough_inc=.28
        else:
            oxide_color=np.array([.315,.128,.073],dtype=np.float32)
            ox_strength=.55
            rough_inc=.38
        modulation=np.clip(.78+.18*wear+.16*fine+.07*micro,.55,1.22)
        rough=np.clip(roughness+.135*oxide+.10*caverns+
                      .046*fine+.045*micro+rough_inc*.36*oxide,.31,.95)
        metallicmap=np.clip(metallic*(1-ox_strength*oxide-.22*caverns),.12,1.)
        bump=.47+.085*broad+.085*fine+.075*caverns+.055*freckles-.030*scratches
        colored=[1.,1.,1.]
    if surface!="arcane_lithic":
        color=np.stack([np.clip(base[k]*modulation*colored[k],0,1) for k in range(3)],axis=-1)
    if oxide is not None:
        tint_mask=np.clip(oxide*.69+.20*caverns,0,.88)
        color=color*(1-tint_mask[:,:,None])+oxide_color[None,None,:]*tint_mask[:,:,None]
    if surface=="arcane_iron":
        # The door ITSELF is blue-energized cold iron: cloudy mineral diffusion in
        # scattered oxidation pockets, not neon piping or brightly drawn runes.
        clouds=sat((.65*macro+.40*broad+.19*fine+.07)*1.45)
        weathered_blue=sat(.20+.49*clouds+.19*oxide)
        # Keep cold-forged dark iron exposed; blue light originates within patina.
        color[:,:,0]=mix(color[:,:,0],.035,weathered_blue*.18)
        color[:,:,1]=mix(color[:,:,1],.115,weathered_blue*.22)
        color[:,:,2]=mix(color[:,:,2],.240,weathered_blue*.24)
        # V022: strong cyan glow baked into the DOOR'S PBR emission map itself.
        # No neon tubing, no opaque overlay meshes; wide weathered mineral pools
        # and luminous micro-pits transition softly across the real iron texture.
        # Patchy sub-surface illumination: dark steel remains visible over most
        # of the leaf. Only cloudy areas with higher mineral activity fluoresce.
        # This is a genuine textured emission map, not extra neon geometry.
        # V022: irregular inner mineral veins and isolated oxidized pockets,
        # physically within the image-space PBR emission. Not geometry or neon.
        energy=.62*macro+.42*broad+.20*fine+.10*pore
        fracture=np.exp(-((energy-.15)/.075)**2)*sat(.42+.68*macro+.20*broad)
        pockets=sat((energy-.52)/.38)**2.1
        penumbra=sat((energy-.20)/.68)**2
        glow=sat((.72*fracture+.90*pockets+.09*penumbra)*
                 sat(.85+.16*freckles+.13*fine))
        emission=np.stack((.012*glow,.69*glow,1.0*glow),axis=-1)
        print("V022_TEXTURED_GLOW_COVERAGE",name,
              float(np.mean(glow>.15)),float(np.mean(glow>.60)),
              float(np.mean(glow)),flush=True)
    # OpenGL (+Y) tangent-space normal map, derivatives of genuine procedural height.
    dx=np.gradient(bump,axis=1)*3.6
    dy=np.gradient(bump,axis=0)*3.6
    length=np.sqrt(dx*dx+dy*dy+1)
    normal=np.stack((.5-.5*dx/length,.5-.5*dy/length,
                     .5+.5/length),axis=-1)
    def write_img(kind,rgb,linear):
        im=bpy.data.images.new(name+"_"+kind,width=n,height=n,alpha=True)
        if rgb.ndim==2:rgb=np.repeat(rgb[:,:,None],3,axis=2)
        rgba=np.concatenate((np.asarray(rgb,dtype=np.float32),
                             np.ones((n,n,1),dtype=np.float32)),axis=2)
        im.pixels.foreach_set(sat(rgba).ravel())
        im.filepath_raw=str(OUT/(name+"_"+kind+".png"))
        im.file_format="PNG";im.save()
        if linear:im.colorspace_settings.name="Non-Color"
        im.pack()
        return im
    al=write_img("albedo",color,False)
    rm=write_img("roughness",rough,True)
    nm=write_img("normal",normal,True)
    mm=write_img("metallic",metallicmap,True)
    nodes=m.node_tree.nodes;links=m.node_tree.links
    for img,socket in ((al,"Base Color"),(rm,"Roughness"),(mm,"Metallic")):
        node=nodes.new("ShaderNodeTexImage");node.image=img
        links.new(node.outputs["Color"],bs.inputs[socket])
    norm_node=nodes.new("ShaderNodeTexImage");norm_node.image=nm
    tangent=nodes.new("ShaderNodeNormalMap")
    tangent.inputs["Strength"].default_value=.95
    links.new(norm_node.outputs["Color"],tangent.inputs["Color"])
    links.new(tangent.outputs["Normal"],bs.inputs["Normal"])
    if emission is not None:
        em=write_img("emission",emission,False)
        emnode=nodes.new("ShaderNodeTexImage");emnode.image=em
        links.new(emnode.outputs["Color"],bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value=float(os.environ.get("PG_ARCANE_EMISSIVE_STRENGTH","6.0"))
    # Flag real material variance for CI: flat-color textures are rejected.
    metrics={"albedo_std":float(color.std(axis=(0,1)).mean()),
             "rough_std":float(rough.std()),
             "normal_x_std":float(normal[:,:,0].std()),
             "metallic_std":float(metallicmap.std()),
             "has_emission":emission is not None}
    with (OUT/(name+"_PBR_QA.json")).open("w") as out:
        json.dump(metrics,out,indent=2)
    assert metrics["albedo_std"]>.009,(name,metrics)
    assert metrics["rough_std"]>.025,(name,metrics)
    assert metrics["normal_x_std"]>.006,(name,metrics)
    return m

def themed(role,seed):
    base,metallic,roughness,surface=PROFILES[TRADE][role]
    return material("v022_"+TRADE+"_"+role,base,metallic,roughness,seed,surface)

iron=themed("leaf",17)
edge=themed("edge",18)
copper=themed("hardware",19)
shade=themed("inset",20)

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
        cube("Forged_panel_vertical_lip",(sx*.438,-.104,z),(.017,.033,h-.005),edge,.004)
    for zz in (z0,z1):
        cube("Forged_panel_horizontal_lip",(0,-.104,zz),(.877,.034,.019),edge,.004)
    for sx in (-1,1):
        for zz in (z0+.052,z1-.052):rivet(sx*.374,zz,-.116,.012)
# Six riveted shoulder and base forged rails
for z in (.11,1.805):
    cube("Heavy_merchant_shop_crossbar",(0,-.090,z),(1.035,.055,.053),edge,.009)
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
stroke("Arch_centre_leaf",[(-.032,-.122,2.06),(0,-.123,2.145),(.032,-.122,2.06)],.010,edge)
# Lower forged scrolls, recessed within last metal panel.
for side in (-1,1):
    scroll("Lower_shop_scroll",side*.23,.36,.12,1.12,-side,-.114,edge)
    scroll("Lower_end_scroll",side*.39,.36,.055,.86,side,-.113,edge)
    stroke("Lower_scroll_sweeping_base",[
        (side*(.035+.43*t/75),-.116,.33+.105*sin(pi*t/75)) for t in range(76)],.009,edge)
# Hinges: two decorative leaf shaped straps on left, with actual barrel and riveted pins.
for z in (.455,1.295):
    cylinder("Functional_vertical_hinge_barrel",(-.603,-.008,z),.036,.184,edge,verts=20)
    for dz in (-.086,.086):
        cylinder("Handforge_hinge_collar",(-.603,-.008,z+dz),.045,.019,iron,verts=20)
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
ring("Peephole_lid_ridge",-.194,CENTER_PEEP,.053,-.179,.005,edge)
for dz in (-.038,.038):
    cylinder("Peephole_lid_vertical_pivot",(-.108,-.150,CENTER_PEEP+dz),.011,.038,edge,verts=12)
# ONE practical copper-brass LEVER on the right: shaft and handle are independent.
cube("Right_handle_copper_mount",(.454,-.110,HANDLE_Z),(.088,.028,.102),copper,.014)
cylinder("Right_handle_pivot_hub",(.454,-.145,HANDLE_Z),.037,.056,copper,(pi/2,0,0),32)
stroke("One_right_brass_horizontal_turning_lever",[(.443,-.184,HANDLE_Z),(.365,-.200,HANDLE_Z),
(.270,-.201,HANDLE_Z+.004),(.232,-.195,HANDLE_Z+.006)],.022,copper)
cylinder("One_lever_end_finish",(.232,-.195,HANDLE_Z+.006),.024,.025,copper,(0,pi/2,0),24)
# Selective hand-struck surface dents on four exposed iron panels (no crude tiled stones).
for zcentre,height in ((.415,.46),(1.01,.50),(1.55,.30)):
    for k in range(15):
        x=random.uniform(-.34,.34)
        z=zcentre+random.uniform(-height*.42,height*.42)
        if (x*x+(z-CENTER_PEEP)**2)<.020: continue
        y=-.100-random.uniform(.001,.003)
        ln=random.uniform(.008,.027)
        stroke("Irregular_short_hammer_scar",[(x-ln/2,y,z-.0008),(x+ln/2,y,z+.0008)],
            random.uniform(.00055,.0011),shade)
# Brass is patinated; pin heads vary in size and are not ornamental copper dots.
# Functional key escutcheon below turning lever.
cube("Hand-wrought lock cover plate",(.435,-.117,.897),(.062,.018,.109),edge,.009)
cube("Actual deep keyway shadow",(.435,-.130,.909),(.010,.004,.051),shade,.002)
cylinder("Keyhole bowl",(.435,-.131,.938),.010,.004,shade,(math.pi/2,0,0),16)
# V008 X-braces ended in open air, above/below the actual horizontal rails.
# V011 extends all four diagonal ends INTO the upper/lower structural straps
# and adds peened anchor plates so the rear stiffeners are mechanically held.
for z in (.225,.940,1.815):
    cube("Interior_forged_crossbrace",(0,.090,z),(1.02,.038,.055),iron,.006)
for side in (-1,1):
    stroke("Interior_diagonal_stiffener",[
        (side*.46,.116,.224),(-side*.46,.116,1.815)],.021,iron)
    for x,z in ((side*.46,.224),(-side*.46,1.815)):
        cube("Structural_rear_brace_end_plate",(x,.133,z),(.095,.025,.071),edge,.008)
        cylinder("Peened_rear_brace_to_rail_anchor",(x,.152,z),.016,.012,copper,
                 (pi/2,0,0),20)
cube("Interior_lock_case",(.44,.11,HANDLE_Z),(.17,.064,.23),edge,.010)

# Material-depth identity on insets. Keep every originally approved door vertex
# intact; optional shallow facade elements stay entirely inside that silhouette.
if TRADE=="carpintero":
    for panel,(z0,z1) in enumerate(((.172,.655),(.725,1.285),(1.352,1.748))):
        h=z1-z0;zc=(z0+z1)/2
        # Narrow fitted vertical boards; the peephole is NOT concealed on upper panel.
        xs=[-.335,-.201,-.067,.067,.201,.335] if panel<2 else [-.335,-.201,.201,.335]
        for k,cx in enumerate(xs):
            cube("Carpenter_oak_board_%d_%d"%(panel,k),
                 (cx,-.101,zc),(.128,.022,h-.059),iron,.004)
elif TRADE=="curtidor":
    # Distinct soft full-grain leather insets held under permanent iron framing.
    for obj in objects:
        if obj.name.startswith("Hand-hammered_twisted_sheet_"):
            obj.data.materials.clear()
            obj.data.materials.append(shade)
    for panel,(z0,z1) in enumerate(((.172,.655),(.725,1.285),(1.352,1.748))):
        zc=(z0+z1)/2;hh=(z1-z0)*.5-.045
        # A subdued stitched perimeter: physically inset beneath the steel lips.
        stroke("Leather_inset_tension_seam_%d"%panel,
               [(-.373,-.111,zc-hh),(.373,-.111,zc-hh),
                (.373,-.111,zc+hh),(-.373,-.111,zc+hh)],
               .0024,edge,True)

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

# UVs must exist BEFORE Cycles preview: otherwise image-node textures can
# collapse to constant samples and misrepresent both mineral PBR and emission.
if TRADE=="arcanista":
    for ob in root.children:
        if ob.type!="MESH": continue
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(island_margin=.015)
        bpy.ops.object.mode_set(mode="OBJECT")
    print("V024_UV_CREATED_BEFORE_RENDER",len(root.children),flush=True)

def light(loc,power,size):
    ld=bpy.data.lights.new("studio area","AREA")
    obj=bpy.data.objects.new("studio area",ld)
    bpy.context.collection.objects.link(obj)
    obj.location=loc
    ld.energy=power;ld.shape="DISK";ld.size=size
    obj.rotation_euler=(Vector((0,0,1.15))-obj.location).to_track_quat("-Z","Y").to_euler()
light((-3,-4,4),1120,4.0)
light((4.8,1.1,2.9),850,3.0)
light((1,-2,3),195,2.4)
light((-2,4.5,3.2),570,4.0)  # Dedicated rear QA fill reveals anchor connections.
sc=bpy.context.scene
sc.render.engine="CYCLES"
sc.cycles.samples=int(os.environ.get("PG_CYCLES_SAMPLES","48"))
bpy.context.view_layer.cycles.use_denoising=True
sc.render.resolution_x=int(os.environ.get("PG_RENDER_WIDTH","1200"))
sc.render.resolution_y=int(os.environ.get("PG_RENDER_HEIGHT","1600"))
sc.render.resolution_percentage=100
sc.render.film_transparent=True
sc.view_settings.view_transform="AgX"
# Optional render-only bloom. The GLB independently retains its emissive map.
try:
    sc.use_nodes=True
    comp=sc.node_tree
    comp.nodes.clear()
    src_node=comp.nodes.new("CompositorNodeRLayers")
    glow_node=comp.nodes.new("CompositorNodeGlare")
    glow_node.glare_type="FOG_GLOW"
    glow_node.quality="HIGH"
    glow_node.threshold=1.6
    glow_node.size=7
    glow_node.mix=-.62
    final_node=comp.nodes.new("CompositorNodeComposite")
    comp.links.new(src_node.outputs["Image"],glow_node.inputs["Image"])
    comp.links.new(glow_node.outputs["Image"],final_node.inputs["Image"])
except Exception as ex:
    print("RENDER_BLOOM_FALLBACK",str(ex),flush=True)
    sc.use_nodes=False
view_specs=[
    ("front_orthographic",(0,-6,1.15)),
    ("three_quarter",(2.3,-5,1.7)),
    ("side_orthographic",(6,0,1.15)),
    ("rear_orthographic",(0,6,1.15)),
]
if os.environ.get("PG_REVIEW_ONLY")=="1":
    view_specs=[("three_quarter",(2.3,-5,1.7))]
for name,pos in view_specs:
    bpy.ops.object.camera_add(location=pos)
    cam=bpy.context.object
    cam.rotation_euler=(Vector((0,0,1.15))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=2.53
    sc.camera=cam;sc.render.filepath=str(OUT/(name+".png"))
    bpy.ops.render.render(write_still=True)

if os.environ.get("PG_REVIEW_ONLY")=="1":
    print("V022_QUICK_PREVIEW_DONE",str(OUT/"three_quarter.png"),flush=True)
    raise SystemExit(0)

# GLB PBR export: only modeled hierarchy; UV unwrap on separate pieces.
bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
for ob in root.children:
    if ob.type=="MESH":
        ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(island_margin=.015)
        bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.export_scene.gltf(filepath=str(OUT/f"Workshop_Door_V022_{TRADE}.glb"),
    export_format="GLB",use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f"Workshop_Door_V022_{TRADE}.blend"))
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
    json.dump({"source":f"V015 material-only proof: {TRADE} on V011 approved door geometry; no private V175 textures",
        "version":"V022","baseline_version":"V010",
        "targeted_repairs":["preserve connected rear structural braces and peephole through-mesh",
                            "reduce tiny rivet cylinders and curve tessellation below silhouette threshold",
                            "reduce hidden hammer plate subdivisions without removing PBR relief",
                            "reduce bevel segments and retain edge catchlights for front and side views"],
        "legacy_meshes_reused":0,"shape":"arched_iron_merchant_shop",
        "true_circular_peep_hole":True,"lever_count":1,"wood":TRADE in ("carpintero","curtidor"),
        "texture_pixels":int(os.environ.get("PG_PBR_RES","2048")),"texture_max_allowed":4096,
        "geometry_budget_target_triangles":25000,"evaluated_triangles":triangles,
        "budget_met":triangles<=25000,
        "note":"Budget is a target, not an automatic art approval; compare silhouette in four views"},f,indent=2)

with (OUT/"V022_MATERIAL_TEST.json").open("w",encoding="utf-8") as f:
    json.dump({"version":"V022","geometry_baseline":"V011_USER_APPROVED",
      "material_goal":f"profession-specific PBR: {TRADE} on approved V011 geometry",
      "source_texture_copied":False,
      "exact_V175_material_applied":False,
      "reason":"V175 original lives in private repository; public preview deliberately uses independently generated proxy",
      "material_only":True,"artist_approval":"PENDING","profession":TRADE,"surface_palette":PROFILES[TRADE]},f,indent=2)
