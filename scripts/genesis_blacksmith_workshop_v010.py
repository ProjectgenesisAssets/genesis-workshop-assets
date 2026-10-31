# Project Genesis / PlayCanvas - distinct workshop wall geometry trials.
# Executed only by Blender 4.5.13 LTS in public GitHub Actions.
# Experimental, neither the wall nor the V011 door is approved here.
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi
import numpy as np

KIND="herrero"
VERSION="v010" if KIND=="herrero" else "v001"
SEED=29012026 if KIND=="herrero" else 29022026
rng=random.Random(SEED)
ROOT=Path("output_workshop_wall_"+KIND+"_"+VERSION).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
INPUT=Path("inputs/wall_"+KIND+"_"+VERSION).resolve()
W,H,T=7.875,3.20,.48
DW,DH=1.48,2.43
PREFIX="ASSET_"
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def image(filename,srgb=True):
    a=bpy.data.images.load(str(INPUT/filename),check_existing=True)
    a.colorspace_settings.name="sRGB" if srgb else "Non-Color"
    return a
def darken_scan(filename,filename_out,factors):
    src=image(filename)
    width,height=src.size[:]
    px=np.empty(width*height*4,dtype=np.float32)
    src.pixels.foreach_get(px)
    arr=px.reshape((-1,4))
    for k in range(3):arr[:,k]=np.clip(arr[:,k]*factors[k],0,1)
    result=bpy.data.images.new(filename_out,width=width,height=height,alpha=False,float_buffer=False)
    result.pixels.foreach_set(px)
    result.filepath_raw=str(ROOT/(filename_out+".jpg"))
    result.file_format="JPEG";result.save()
    result.colorspace_settings.name="sRGB"
    return result
stone_tex=darken_scan("stone_albedo_2k.jpg","herrero_blackened_basalt_2k",(.50,.54,.59))
rough_tex=image("stone_rough_2k.jpg",False)
normal_tex=image("stone_normal_2k.png",False)
wood_tex=darken_scan("wood_albedo_2k.jpg","herrero_charred_oak_2k",(.64,.59,.54))
wood_rough=image("wood_rough_2k.jpg",False)
wood_normal=image("wood_normal_2k.png",False)

def pbr(name,alb,rgh,nrm,tint,normal_strength=1.0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree;bs=nt.nodes.get("Principled BSDF")
    al=nt.nodes.new("ShaderNodeTexImage");al.image=alb
    mix=nt.nodes.new("ShaderNodeMixRGB");mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1.0
    mix.inputs[2].default_value=(tint[0],tint[1],tint[2],1)
    nt.links.new(al.outputs["Color"],mix.inputs[1]);nt.links.new(mix.outputs[0],bs.inputs["Base Color"])
    rn=nt.nodes.new("ShaderNodeTexImage");rn.image=rgh
    nt.links.new(rn.outputs["Color"],bs.inputs["Roughness"])
    nn=nt.nodes.new("ShaderNodeTexImage");nn.image=nrm
    nm=nt.nodes.new("ShaderNodeNormalMap");nm.inputs["Strength"].default_value=normal_strength
    nt.links.new(nn.outputs["Color"],nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    return m

if KIND=="herrero":
    rocks=[
        pbr("Quarry basalt / dark warm PBR",stone_tex,rough_tex,normal_tex,(.42,.37,.34),1.1),
        pbr("Basalt - mineral warm variance",stone_tex,rough_tex,normal_tex,(.49,.41,.35),1.1),
        pbr("Soot deposits - char and oxide",stone_tex,rough_tex,normal_tex,(.30,.31,.30),1.1),
    ]
    timber=pbr("Oak / fire seasoned PBR",wood_tex,wood_rough,wood_normal,(.46,.36,.29),1.05)
else:
    rocks=[
        pbr("Metamorphic slate / charcoal-blue PBR",stone_tex,rough_tex,normal_tex,(.30,.37,.43),1.15),
        pbr("Slate / subtle iron blue inclusions",stone_tex,rough_tex,normal_tex,(.38,.45,.49),1.15),
        pbr("Slate / deep fracture",stone_tex,rough_tex,normal_tex,(.21,.27,.32),1.15)
    ]
    timber=pbr("Weathered hidden structural wood PBR",wood_tex,wood_rough,wood_normal,(.30,.31,.30))
iron=bpy.data.materials.new("Oxidized forged iron");iron.use_nodes=True
ib=iron.node_tree.nodes.get("Principled BSDF")
ib.inputs["Base Color"].default_value=(.085,.076,.071,1)
ib.inputs["Metallic"].default_value=.72
ib.inputs["Roughness"].default_value=.68
mortar=bpy.data.materials.new("Recessed stone mortar / dark");mortar.use_nodes=True
mb=mortar.node_tree.nodes.get("Principled BSDF")
mb.inputs["Base Color"].default_value=(.056,.057,.062,1) if KIND=="arcanista" else (.11,.097,.088,1)
mb.inputs["Roughness"].default_value=.93

def cube(name,loc,dims,material,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=bpy.context.object;ob.name=PREFIX+name;ob.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(material)
    if bevel>0:
        mod=ob.modifiers.new("worn corners","BEVEL");mod.width=bevel;mod.segments=2
        ob.modifiers.new("weighted normals","WEIGHTED_NORMAL")
    return ob

def sculpt_block(name,x0,x1,z0,z1,kind=0,depth=None,dist=.030):
    # Eight rounded, individually displaced perimeter points and an uneven face.
    # Unlike the rejected V003 Voronoi tests, blocks follow masonry courses or
    # long geological strata. No hexagonal tessellation or procedural honeycomb.
    wid=x1-x0;hei=z1-z0
    if wid<.065 or hei<.055:return None
    cx=(x0+x1)*.5;cz=(z0+z1)*.5
    spread=min(dist,wid*.055,hei*.052)
    px=[(x0,z0),(cx,z0),(x1,z0),(x1,cz),(x1,z1),(cx,z1),(x0,z1),(x0,cz)]
    ring=[]
    for k,(x,z) in enumerate(px):
        fx=(rng.random()-.5)*spread
        fz=(rng.random()-.5)*spread
        ring.append((x+fx,z+fz))
    front=depth if depth is not None else -.285-rng.uniform(.002,.025)
    verts=[(cx,front-rng.uniform(.006,.017),cz)]
    for x,z in ring:verts.append((x,front+rng.uniform(-.008,.009),z))
    for x,z in ring:verts.append((x,-.085+rng.uniform(-.015,.015),z))
    faces=[(0,1+i,1+((i+1)%8)) for i in range(8)]
    faces.extend([(1+i,9+i,9+((i+1)%8),1+((i+1)%8)) for i in range(8)])
    faces.append(tuple(range(16,8,-1)))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(PREFIX+name,me);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(rocks[kind%len(rocks)])
    uv=me.uv_layers.new(name="UVMap")
    for pol in me.polygons:
        for li in pol.loop_indices:
            p=me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv=((p.x+W/2)/2.2,p.z/2.15)
    for pol in me.polygons:pol.use_smooth=False
    return ob

# Dark structural core; no blank bright sides or glaring top slab.
for name,x0,x1,z0,z1 in [
    ("left",-W/2,-DW/2,0,H),("right",DW/2,W/2,0,H),
    ("head",-DW/2,DW/2,DH,H)
]:
    cube("Structural_"+name,((x0+x1)/2,.06,(z0+z1)/2),(x1-x0,T,z1-z0),mortar,.009)

def courses(zone,x0,x1,z0,z1):
    z=z0;row=0
    while z < z1-.055:
        h=min(rng.uniform(.32,.59) if KIND=="herrero" else rng.uniform(.69,1.15),z1-z)
        if z1-z-h<.12:h=z1-z
        x=x0;col=0
        while x<x1-.05:
            w=min(rng.uniform(.57,1.36) if KIND=="herrero" else rng.uniform(.86,1.72),x1-x)
            if x1-x-w<.21:w=x1-x
            inset=.009 if KIND=="herrero" else .016
            shade=rng.choices([0,1,2],weights=[6,2,2])[0]
            if abs(x+w*.5)<1.8 and z>DH-.55:shade=2
            sculpt_block(zone+"_"+str(row)+"_"+str(col),x+inset/2,x+w-inset/2,
                         z+inset/2,z+h-inset/2,shade,dist=.035 if KIND=="herrero" else .085)
            x+=w;col+=1
        z+=h;row+=1
courses("L",-W/2,-DW/2,0,H)
courses("R",DW/2,W/2,0,H)
courses("OverDoor",-DW/2,DW/2,DH,H)

def bolt(name,xyz):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.036,location=xyz)
    ob=bpy.context.object;ob.name=PREFIX+name;ob.data.materials.append(iron)
def stone_cap(name,loc,dims):
    o=cube(name,loc,dims,rocks[rng.choice([0,1])],.023)
    o.rotation_euler[1]=rng.uniform(-.016,.016)
    return o

if KIND=="herrero":
    # Articulated wall: chunky quarried foundation, smoke-worn heavy oak,
    # forging hardware. Flat decorative blocks are expressly avoided.
    for side in (-1,1):
        # Load bearing quoins are continuous masonry members, not a
        # stack of disconnected boulders. Depth and corner setbacks
        # read as structural mass rather than precarious floating rocks.
        stone_cap("LoadBearingCornerPier_"+str(side),
                  (side*(W/2-.16),-.35,H*.5),(.50,.48,H-.05))
        # The approved V011 opening stays completely clear.
        stone_cap("LoadBearingDoorPier_"+str(side),
                  (side*(DW/2+.21),-.385,DH*.5),(.40,.50,DH-.045))
        o=cube("OakOuterPost_"+str(side),(side*(W/2-.39),-.39,1.57),(.18,.29,2.94),timber,.016)
        o=cube("IronStrapUpper_"+str(side),(side*(W/2-.39),-.545,2.49),(.27,.06,.20),iron,.008)
        bolt("CornerStrapRivet_"+str(side),(side*(W/2-.39),-.587,2.49))
        o=cube("CornerIronBrace_"+str(side),(side*(W/2-.39),-.55,.52),(.25,.055,.25),iron,.008)
        bolt("LowerRivet_"+str(side),(side*(W/2-.39),-.585,.52))
    # The cap and lintel now have a substantial actual quarry-stone silhouette.
    stone_cap("WeightBearingLintel",(0,-.37,DH+.155),(DW+.74,.44,.29))
    for side in (-1,1):
        stone_cap("LintelSaddle_"+str(side),(side*(DW/2+.37),-.36,DH+.145),(.34,.39,.34))
    oakbeam=cube("TimberTopBrace",(0,-.41,H-.17),(W-.8,.27,.19),timber,.011)
    for side in (-1,1):
        cube("HammeredTopIron_"+str(side),(side*2.5,-.57,H-.17),(.27,.064,.27),iron,.011)
        bolt("TopBolt_"+str(side),(side*2.5,-.611,H-.17))
    # A heavy continuous load-bearing plinth replaces the loose ground
    # stones, with no gaps under the structural pillars.
    for side in (-1,1):
        x0=(-W/2 if side<0 else DW/2)
        x1=(-DW/2 if side<0 else W/2)
        stone_cap("SolidStoneFoundation_"+str(side),
                  ((x0+x1)*.5,-.33,.165),(x1-x0,.49,.33))
        # One narrow weathering edge provides a visible bedding plane.
        cube("PlinthWeatheringEdge_"+str(side),
             ((x0+x1)*.5,-.576,.305),
             (x1-x0,.018,.024),rocks[2],.005)
    # True stone coping covers the exposed white structural rear slab.
    x=-W/2;k=0
    while x<W/2-.10:
        wid=min(rng.uniform(.74,1.38),W/2-x)
        if W/2-x-wid<.28:wid=W/2-x
        top=stone_cap("WeatheredFullDepthCoping_"+str(k),
                      (x+wid*.5,.0,H+.068),(wid-.018,T+.13,.155))
        top.rotation_euler[1]=rng.uniform(-.013,.013)
        x+=wid;k+=1
else:
    # The arcanist's entrance grows out of shale; NO wooden rectangular frame.
    # Crystalline slate piers overlap surrounding wall, never the actual door.
    for side in (-1,1):
        for i in range(6):
            z=.23+i*.40
            x=side*(DW/2+.18+(.023 if i%2 else -.025))
            b=stone_cap("MonolithicJamb_%s_%s"%(side,i),(x,-.40,z),
                        (.32,.38,rng.uniform(.35,.48)))
            b.rotation_euler[1]=side*rng.uniform(-.065,.065)
        for i in range(3):
            z=.55+i*.96
            x=side*(W/2-.29)
            b=stone_cap("SlateButtress_%s_%s"%(side,i),(x,-.34,z),
                        (.46,.30,rng.uniform(.76,1.0)))
            b.rotation_euler[1]=rng.uniform(-.075,.075)
    # A shallow irregular stone arch above the rectangular approved door:
    # the opening stays compatible with V011, but no ugly rectangular frame.
    for i in range(13):
        th=pi-i*pi/12
        rr=1.07
        x=rr*cos(th)
        z=DH+.05+.57*sin(th)
        b=stone_cap("ArcFragment_%02d"%i,(x,-.44,z),(.31,.42,.34))
        b.rotation_euler[1]=(.5*pi-th)*.28+rng.uniform(-.10,.10)
    # Hairline mineral energy, contained in naturally fractured stone, not neon.
    glow=bpy.data.materials.new("Buried arcane light / desaturated blue");glow.use_nodes=True
    bs=glow.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(.026,.095,.13,1)
    bs.inputs["Emission Color"].default_value=(.015,.14,.23,1)
    bs.inputs["Emission Strength"].default_value=1.0
    bs.inputs["Roughness"].default_value=.5
    def filament(n,pts):
        cv=bpy.data.curves.new("StoneFissure_"+n,"CURVE")
        cv.dimensions='3D';cv.resolution_u=1
        cv.bevel_depth=.008;cv.resolution_u=1;cv.bevel_resolution=1
        spl=cv.splines.new('POLY');spl.points.add(len(pts)-1)
        for pt,xyz in zip(spl.points,pts):
            pt.co=(xyz[0],xyz[1],xyz[2],1)
        ob=bpy.data.objects.new(PREFIX+"Fissure_"+n,cv)
        bpy.context.collection.objects.link(ob);ob.data.materials.append(glow)
        bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        bpy.ops.object.convert(target="MESH");ob.select_set(False)
    # Sparse fracture trails branch only near the door arch. Door texture
    # itself is not touched and is the source of its own GLB animation.
    for side in (-1,1):
        for n in range(3):
            x=side*(.99+.16*n)
            z=.53+n*.63
            pts=[(x,-.592,z-.25),(x+side*.027,-.598,z-.11),
                 (x-side*.034,-.602,z+.08),(x+side*.05,-.598,z+.22)]
            filament("%s_%s"%(side,n),pts)
    for n in range(4):
        x=-.76+n*.48;z=DH+.46+.08*sin((n+1)*1.6)
        filament("Arch_%s"%n,[(x-.10,-.653,z-.06),(x,-.66,z),(x+.09,-.651,z+.055)])
    # Deliberately irregular roofline, to echo the sculpted arc without being
    # an oversized square monolith.
    for i in range(8):
        x=-W/2+(i+.5)*W/8
        if abs(x)<1.2:continue
        cap=stone_cap("WeatheredCoping_"+str(i),(x,-.31,H-.045),
                       (W/8-.015,.40,rng.uniform(.11,.19)))
        cap.rotation_euler[1]=rng.uniform(-.035,.035)


# ========== V010: 3 new walls and 4 real structural corners ==========
# Blender coordinates: X left/right, Y depth toward the rear, Z up.
# The original V006 FRONT masonry above has NOT been remodeled.
# In PlayCanvas the old shell is 12 x 10.5 local units with .75 X/Z scale:
# these pieces use the ratio 7.875/12, and need measured final placement
# relative to the approved off-center door before gameplay integration.
from mathutils import Matrix
DEPTH=6.890625
front_objects={o.name for o in bpy.data.objects if o.name.startswith(PREFIX)}
# Keep every original V006 exterior stone and beam. Only ADD a genuinely
# mineral inner surface to the existing front, keeping the door cutout.
def inner_front_stones(label,x0,x1,z0,z1):
    before={o.name for o in bpy.data.objects}
    courses("FRONT_INNER_"+label,x0,x1,z0,z1)
    for ob in bpy.data.objects:
        if ob.name not in before and ob.type=="MESH" and ob.name.startswith(PREFIX):
            for v in ob.data.vertices:v.co.y=-v.co.y+.035
            ob.data.update()
            front_objects.add(ob.name)
inner_front_stones("LEFT",-W/2,-DW/2,0,H)
inner_front_stones("RIGHT",DW/2,W/2,0,H)
inner_front_stones("LINTEL",-DW/2,DW/2,DH,H)
# Dress the interior-facing exposed sides of the doorway; the insert sits
# OUTSIDE the original collision aperture and does not touch V011.
front_returns_before={o.name for o in bpy.data.objects if o.name.startswith(PREFIX)}
for side in (-1,1):
    cube("StoneDoorReturn_"+str(side),
         (side*(DW/2+.042),.06,DH*.5),(.083,T-.025,DH-.055),
         revealmat,.007)
cube("StoneDoorHeaderReturn",(0,.06,DH+.042),
     (DW+.18,T-.025,.082),revealmat,.007)
for ob in bpy.data.objects:
    if ob.name.startswith(PREFIX) and ob.name not in front_returns_before:
        front_objects.add(ob.name)

# Dense soot-blackened cap with procedural mineral grain. The exposed top
# plane previously sampled a nearly white portion of the photo texture, which
# looked like an unfinished concrete strip. Preserve all silhouettes while
# assigning a uniquely dark, non-metallic charcoal-stone material.
# Use the SAME Poly Haven scanned basalt as the structural masonry.
# The previous light procedural material turned nearly white under Cycles.
# This is one-third the main wall's albedo, not an untextured flat shader.
capmat=pbr("Blackened ironstone coping / dark scanned PBR",
           stone_tex,rough_tex,normal_tex,(.085,.077,.071),1.2)
revealmat=pbr("Deep-set door reveals / soot scanned basalt PBR",
              stone_tex,rough_tex,normal_tex,(.13,.12,.105),1.25)

# Stone coping in V006 was washed out in the review light. Swap only
# its exposed material to the soot-dark scanned basalt, no silhouette change.
for ob in bpy.data.objects:
    if ob.name.startswith(PREFIX+"WeatheredFullDepthCoping_") and ob.type=="MESH":
        ob.data.materials.clear()
        ob.data.materials.append(capmat)
segments={}
# A physical dark window insert rather than a paper-white hole; frame and
# narrow forged bars keep the side of the working smithy visibly believable.
window_dark=bpy.data.materials.new("Blacksmith · soot-stained grille background")
window_dark.use_nodes=True
wd=window_dark.node_tree.nodes.get("Principled BSDF")
wd.inputs["Base Color"].default_value=(.045,.046,.047,1)
wd.inputs["Roughness"].default_value=.95

def interior_courses(name,x0,x1,z0,z1):
    # Actual carved masonry on the INNER face, not a plain white core.
    # Mirror the existing sculpted stones through Y; this preserves the
    # same scan UV coordinates, correct face normals and genuine depth.
    before={o.name for o in bpy.data.objects}
    courses(name+"_InteriorPBR",x0,x1,z0,z1)
    for ob in bpy.data.objects:
        if ob.name not in before and ob.type=="MESH" and ob.name.startswith(PREFIX):
            for v in ob.data.vertices:
                v.co.y=-v.co.y+.035
            ob.data.update()

def wall_area(name,x0,x1,z0,z1):
    if x1-x0<.04 or z1-z0<.05:return
    cube(name+"_structural",((x0+x1)*.5,.06,(z0+z1)*.5),
         (x1-x0,T,z1-z0),mortar,.008)
    courses(name+"_stone",x0,x1,z0,z1)
    interior_courses(name,x0,x1,z0,z1)

def window_pair(name,cx,low=1.65,high=2.34):
    # Loadbearing masonry outside the window, no painted-on aperture.
    width=.56
    x0,x1=cx-width*.5,cx+width*.5
    cube(name+"_inner_dark",(cx,.07,(low+high)*.5),
         (width-.045,.038,high-low-.03),window_dark,.006)
    for side in (-1,1):
        cube(name+"_stone_jamb_"+str(side),(cx+side*(width*.5+.065),-.32,(low+high)*.5),
             (.14,.25,high-low+.12),rocks[0],.017)
    cube(name+"_head_bearing",(cx,-.33,high+.11),
         (width+.30,.28,.19),rocks[1],.021)
    cube(name+"_sill",(cx,-.36,low-.095),(width+.24,.28,.15),rocks[0],.017)
    for j in (-.16,0,.16):
        cube(name+"_vertical_iron_"+str(round(j,2)),(cx+j,-.394,(low+high)*.5),
             (.018,.044,high-low-.045),iron,.004)

def build_face(name,length,angle,world_x,world_y,windows=(),rear=False):
    # Everything is built with the very same rock/timber PBR library and
    # stone-sculpting function as front V006, then rigidly transformed.
    before=set(bpy.data.objects)
    left=-length*.5;right=length*.5
    breaks=[left]
    for center in windows:
        breaks += [center-.29,center+.29]
    breaks += [right]
    breaks=sorted(breaks)
    for i,(x0,x1) in enumerate(zip(breaks[:-1],breaks[1:])):
        center=(x0+x1)*.5
        is_window=any(abs(center-w)<.3 for w in windows)
        if is_window:
            wall_area(name+"_low_"+str(i),x0,x1,0,1.60)
            wall_area(name+"_upper_"+str(i),x0,x1,2.39,H)
        else:
            wall_area(name+"_solid_"+str(i),x0,x1,0,H)
    for i,w in enumerate(windows):
        window_pair(name+"_window_"+str(i),w)
    # Continuous reinforced base / wall plate: no unsupported floating stones.
    stone_cap(name+"_continuous_plinth",(0,-.25,.125),(length+.08,.53,.25))
    cube(name+"_wall_plate",(0,-.29,H-.105),
         (length-.18,.245,.21),timber,.016)
    # Top is a real dark slate/soot basalt coping, not a bright flat slab.
    cube(name+"_roof_bedding_stone",(0,.02,H+.011),
         (length+.025,T+.10,.115),capmat,.022)
    # The last-course lintel meets the coping seamlessly; dark mineral
    # rather than smooth grey exposed structural core.
    cube(name+"_interior_coping_return",(0,.31,H-.035),
         (length-.12,.10,.14),capmat,.017)
    for side in (-1,1):
        stone_cap(name+"_load_corner_"+str(side),
                  (side*(length*.5-.11),-.31,H*.5),
                  (.37,.46,H-.06))
        cube(name+"_strapped_anchor_"+str(side),
             (side*(length*.5-.12),-.556,H-.36),
             (.26,.051,.20),iron,.01)
        bolt(name+"_anchor_rivet_"+str(side),
             (side*(length*.5-.12),-.59,H-.36))
    if rear:
        # Forge service zone: left clear for V038/hood placement and collision
        # calibration. Only a subtle soot-darkened upper panel, NO fixed forge
        # or invented chimney aperture.
        cube(name+"_dark_smoke_stone",(0,-.333,2.63),
             (1.55,.014,.36),rocks[2],.006)
        # Cross braces sit OUTSIDE the central future forge service zone.
        for side in (-1,1):
            cube(name+"_oak_utility_pier_"+str(side),
                 (side*(length*.5-1.05),-.39,1.42),
                 (.18,.31,2.73),timber,.013)
    new=[o for o in bpy.data.objects if o not in before and o.name.startswith(PREFIX)]
    transform=Matrix.Translation((world_x,world_y,0)) @ Matrix.Rotation(angle,4,'Z')
    for ob in new:
        ob.name=ob.name.replace(PREFIX,PREFIX+name+"_",1)
        ob.matrix_world=transform @ ob.matrix_world
    segments[name]=new
    return new

# The old front facade's physical side spans 7.875; lateral spans match
# the old PlayCanvas shell's 12:10.5 ratio. Roof stays a separate accepted
# asset and is NOT included or modeled here.
build_face("LEFT", DEPTH,-pi/2,-W*.5,DEPTH*.5,windows=(-1.62,1.64))
build_face("RIGHT",DEPTH, pi/2, W*.5,DEPTH*.5,windows=(-1.55,1.55))
build_face("REAR", W,pi,0,DEPTH,windows=(1.72,),rear=True)
# End-cap corner masses join to the already solid front V006 corner piers.
# Rear piers sit inside the outline, never jutting across a pathway.
# These are genuine solid stone supports, not repetitive loose boulders.
# Four-wall circulation inside remains unobstructed by decorative furniture.

def export_only(name,parts):
    selected=[ob for ob in parts if ob.type=='MESH']
    if not selected:raise RuntimeError("Missing component "+name)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in selected:ob.select_set(True)
    bpy.context.view_layer.objects.active=selected[0]
    bpy.ops.export_scene.gltf(filepath=str(ROOT/("genesis_"+name+"_v010.glb")),
       export_format="GLB",use_selection=True,export_texcoords=True,export_normals=True)
    bpy.ops.object.select_all(action="DESELECT")

# Individual components allow collision tests, per-wall LOD and replacement
# without recompiling an enormous all-in-one workshop asset.
for part_name,part_objs in segments.items():
    export_only("blacksmith_wall_"+part_name.lower(),part_objs)
# Keep the V006 front separate for comparing and preserving the accepted shape.
front=[o for o in bpy.data.objects if o.name in front_objects and o.type=="MESH"]
export_only("blacksmith_wall_front_v006",front)
# ========== END V010 ==========

# Review scene is excluded from the GLB.
ground=cube("REVIEW_TEMP",(0,DEPTH*.5,-.085),(11,DEPTH+4,.07),mortar)
ground.name="REVIEW_Ground"
world=bpy.context.scene.world;world.color=(.19,.21,.25)
def light(n,loc,power,size):
    dat=bpy.data.lights.new(n,"AREA");dat.energy=power;dat.shape='DISK';dat.size=size
    ob=bpy.data.objects.new(n,dat);bpy.context.collection.objects.link(ob)
    ob.location=loc;ob.rotation_euler=(Vector((0,0,1.4))-ob.location).to_track_quat("-Z","Y").to_euler()
light("REVIEW_Key",(-4,-6,7),1250,5)
light("REVIEW_Fill",(6,-3,4),720,6)
light("REVIEW_Rim",(0,3,5),850,5)
light("REVIEW_RearFill",(4,DEPTH+7,6.2),680,7)
light("REVIEW_InsideBounce",(0,DEPTH*.5,8),540,6)
bpy.ops.object.camera_add(location=(9,-13,6))
cam=bpy.context.object;cam.name="REVIEW_Camera";cam.data.type='ORTHO'
sc=bpy.context.scene;sc.camera=cam
sc.render.engine='CYCLES';sc.cycles.samples=30
bpy.context.view_layer.cycles.use_denoising=True
sc.render.resolution_x=1400;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.view_settings.view_transform='AgX'
sc.render.film_transparent=False

# Convert ALL curves prior to selection and export? Filaments were converted.
objects=[ob for ob in sc.objects if ob.name.startswith(PREFIX) and ob.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
basename="genesis_wall_"+KIND+"_"+VERSION
bpy.ops.export_scene.gltf(filepath=str(ROOT/(basename+".glb")),export_format='GLB',
                           use_selection=True,export_texcoords=True,export_normals=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(basename+".blend")))

def camera(position,target,scale):
    cam.location=position
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.ortho_scale=scale
shots=[
 ("front",(0,-16,6.8),(0,DEPTH*.3,1.45),13.0),
 ("three_quarter",(12,-15,8.0),(0,DEPTH*.45,1.5),14.0),
 ("right_side",(14,DEPTH*.43,6.8),(0,DEPTH*.48,1.55),12.8),
 ("rear",(8,DEPTH+15,6.5),(0,DEPTH*.55,1.6),14.0),
 ("cutaway",(0,-6,15.4),(0,DEPTH*.52,1.1),13.0),
 ("detail",(7,-3.3,4.5),(W*.5,1.3,1.95),6.5)]

for label,p,t,s in shots:
    camera(p,t,s);sc.render.filepath=str(ROOT/(label+".png"));bpy.ops.render.render(write_still=True)
audit=dict(asset=basename,status="EXPERIMENTAL_NOT_APPROVED",profession=KIND,
           scope="FOUR_WALLS_INTERIOR_EXTERIOR_PBR_NO_ROOF_NO_FORGE",
           depth_m=DEPTH,
           finished_parts=["front_v006","left","right","rear"],
           independent_glbs={name:(ROOT/("genesis_blacksmith_wall_"+name.lower()+"_v010.glb")).stat().st_size for name in segments},
           roof_alignment="PENDING_PLAYCANVAS_VISUAL_TEST",
           interior_masonry="REAL_GEOMETRY_SAME_PBR_PALLETTE",
           roof_seating="SCANNED_PBR_BLACKENED_CHARCOAL_IRONSTONE",
           door_returns="DARK_BASALT_PBR_NO_CLEARANCE_LOSS",
           blender_textures="PACKED_IN_BLEND",
           forge_v038_clearance="PENDING_COLLISION_AND_VISUAL_TEST",
           width_m=W,height_m=H,door_cutout_m=[DW,DH],
           current_door_geometry="V011 not modified",
           geometry="Exterior plus physically sculpted interior PBR masonry; narrower roof-top reveals" if KIND=="herrero" else "Metamorphic slate slabs with carved arch",
           textures="PolyHaven scanned PBR 2K CC0, base/normal/rough",
           visual_review="PENDING",texture_resolution=2048,
           mesh_count=len(objects),triangles=sum(len(p.vertices)-2 for ob in objects for p in ob.data.polygons),
           glb_bytes=(ROOT/(basename+".glb")).stat().st_size,
           previews=[q[0] for q in shots],seed=SEED)
(ROOT/"AUDIT.json").write_text(json.dumps(audit,indent=2))
print("GENESIS_WALL_COMPLETE",json.dumps(audit))
