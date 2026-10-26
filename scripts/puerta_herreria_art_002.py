# New independent art-guided door. No geometry imported or reused from earlier door versions.
# Blender 4.5 / PlayCanvas GLB; all scene generation runs in GitHub Actions.
import bpy, math, json, random
from math import sin, cos, pi
from pathlib import Path
from mathutils import Vector
import numpy as np

OUT=Path("output_blacksmith_door_art_002")
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
random.seed(26)

# Dimensions reference hero: width 1.2 m, max height 2.31 m, 0.104 m thick.
WIDTH=1.20
BASE=.035
SPRING=1.775
RISE=.525
FRONT=-.057
BACK=.057
CENTER_PEEP=1.52
HANDLE_Z=1.035

def material(name, base, metallic, roughness, seed):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*base,1)
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Metallic"].default_value=metallic
    bs.inputs["Roughness"].default_value=roughness
    n=1024  # detailed, web-friendly 1K directional iron PBR source
    rng=np.random.default_rng(seed)
    lows=rng.normal(0,1,(math.ceil(n/12),math.ceil(n/12))).astype(np.float32)
    cloud=np.repeat(np.repeat(lows,12,axis=0),12,axis=1)[:n,:n]
    for _ in range(8):
        cloud=(cloud*4+np.roll(cloud,1,0)+np.roll(cloud,-1,0)+np.roll(cloud,1,1)+np.roll(cloud,-1,1))/8
    micro=rng.normal(0,1,(n,n)).astype(np.float32)
    aging=np.clip(.06+.08*cloud+.025*micro,0,.16)
    shade=np.clip(1+.095*cloud+.032*micro, .79, 1.18)
    color=np.stack([np.clip(base[k]*shade*(1-aging),0,1) for k in range(3)],axis=-1)
    rough=np.clip(roughness+.045*cloud+.015*micro,.22,.89)
    bump=np.clip(.50+.14*cloud+.035*micro,0,1)
    nx=-np.gradient(bump,axis=1)*2.1
    ny=-np.gradient(bump,axis=0)*2.1
    nz=np.ones_like(nx)
    lng=np.sqrt(nx*nx+ny*ny+nz*nz)
    normal=np.stack([.5+.5*nx/lng,.5+.5*ny/lng,.5+.5*nz/lng],axis=-1)
    def map_img(kind,rgb,linear):
        im=bpy.data.images.new(name+"_"+kind,width=n,height=n,alpha=True)
        rgba=np.concatenate([rgb.astype(np.float32),np.ones((n,n,1),dtype=np.float32)],axis=2)
        im.pixels.foreach_set(np.clip(rgba,0,1).ravel())
        im.filepath_raw=str(OUT/(name+"_"+kind+".png"))
        im.file_format="PNG"
        im.save()
        if linear: im.colorspace_settings.name="Non-Color"
        im.pack()
        return im
    c=map_img("albedo",color,False)
    r=map_img("roughness",np.repeat(rough[:,:,None],3,axis=2),True)
    b=map_img("normal",normal,True)
    nodes=m.node_tree.nodes
    cl=nodes.new("ShaderNodeTexImage");cl.image=c
    rl=nodes.new("ShaderNodeTexImage");rl.image=r
    nl=nodes.new("ShaderNodeTexImage");nl.image=b
    nm=nodes.new("ShaderNodeNormalMap");nm.inputs["Strength"].default_value=.34
    links=m.node_tree.links
    links.new(cl.outputs["Color"],bs.inputs["Base Color"])
    links.new(rl.outputs["Color"],bs.inputs["Roughness"])
    links.new(nl.outputs["Color"],nm.inputs["Color"])
    links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    return m

iron=material("iron_aged_hammered",(.155,.151,.142),.85,.57,17)
edge=material("iron_highlights",(.243,.229,.202),.84,.48,18)
copper=material("copper_brass",(.49,.25,.124),.82,.38,19)
shade=material("iron_inset_recess",(.074,.069,.067),.83,.66,20)
objects=[]
def keep(o):
    objects.append(o)
    return o
def bevel(o,w=.006,seg=3):
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
def cylinder(name,loc,r,d,mat,orientation=(0,0,0),verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc,rotation=orientation)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat);bevel(o,min(.004,r*.12),2)
    return keep(o)
def stroke(name,coords,rad,mat,closed=False):
    c=bpy.data.curves.new(name,"CURVE");c.dimensions="3D"
    c.bevel_depth=rad;c.bevel_resolution=3;c.resolution_u=16
    s=c.splines.new("POLY");s.points.add(len(coords)-1)
    for point,xyz in zip(s.points,coords):point.co=(*xyz,1)
    s.use_cyclic_u=closed
    ob=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return keep(ob)
def ring(name,x,z,r,y,thick,mat):
    return stroke(name,[(x+r*cos(2*pi*k/96),y,z+r*sin(2*pi*k/96)) for k in range(96)],thick,mat,True)
def scroll(name,x,z,r,turns,direction,yy,mat):
    coords=[]
    for i in range(95):
        t=i/94
        a=turns*2*pi*t
        radius=r*(1-.92*t)
        coords.append((x+direction*radius*cos(a),yy,z+radius*sin(a)))
    return stroke(name,coords,.008,mat)
def rivet(x,z,y=-.115,r=.013):
    cylinder("Peened forged rivet",(x,y,z),r,.014,copper if r<.011 else edge,(pi/2,0,0),20)

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
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.063,depth=.35,
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
bevel(door,.007)
# Machine-made shape rejected: asymmetric, smoothly rolled hand-forged inner and outer rim.
stroke("Outer_arch_rolled_rim",[(x,-.081,z) for x,z in outline],.020,edge,True)
stroke("Inner_arch_raised_bead",[(x*.927,-.090,BASE+(z-BASE)*.958) for x,z in outline],.006,edge,True)
# Three genuinely recessed planar iron panels with inset bevel borders. No wooden planks.
for i,(z0,z1) in enumerate(((.172,.655),(.725,1.285),(1.352,1.748))):
    h=z1-z0;z=(z1+z0)/2
    cube("Deep_sharp_shadow_inset_%d"%i,(0,-.064,z),(.855,.018,h),shade,.014)
    cube("Hammered_plate_%d"%i,(0,-.086,z),(.817,.019,h-.040),iron,.016)
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
for z in (.455,1.585):
    cylinder("Functional_vertical_hinge_barrel",(-.603,-.008,z),.036,.184,edge,verts=28)
    for dz in (-.086,.086):
        cylinder("Handforge_hinge_collar",(-.603,-.008,z+dz),.045,.019,iron,verts=28)
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
cylinder("Peephole_lid_open",(-.194,-.166,CENTER_PEEP),.065,.015,copper,(pi/2,0,0),48)
ring("Peephole_lid_ridge",-.194,CENTER_PEEP,.053,-.179,.005,edge)
for dz in (-.038,.038):
    cylinder("Peephole_lid_vertical_pivot",(-.108,-.150,CENTER_PEEP+dz),.011,.038,edge,verts=18)
# ONE practical copper-brass LEVER on the right: shaft and handle are independent.
cube("Right_handle_copper_mount",(.454,-.110,HANDLE_Z),(.088,.028,.102),copper,.014)
cylinder("Right_handle_pivot_hub",(.454,-.145,HANDLE_Z),.037,.056,copper,(pi/2,0,0),32)
stroke("One_right_brass_horizontal_turning_lever",[(.443,-.184,HANDLE_Z),(.365,-.200,HANDLE_Z),
(.270,-.201,HANDLE_Z+.004),(.232,-.195,HANDLE_Z+.006)],.022,copper)
cylinder("One_lever_end_finish",(.232,-.195,HANDLE_Z+.006),.024,.025,copper,(0,pi/2,0),24)
# Interior reinforcement is readable from the rear view.
for z in (.225,.940,1.815):
    cube("Interior_forged_crossbrace",(0,.090,z),(1.02,.038,.055),iron,.006)
for side in (-1,1):
    stroke("Interior_diagonal_stiffener",[
        (side*.43,.098,.28),(-side*.43,.098,1.65)],.017,iron)
cube("Interior_lock_case",(.44,.11,HANDLE_Z),(.17,.064,.23),edge,.010)

# An export hierarchy built for a hinge-animated GLB.
root=bpy.data.objects.new("DoorRoot_animate_rotation_about_left_vertical_axis",None)
bpy.context.collection.objects.link(root)
root.location=(-.603,0,0)
for ob in objects:
    mx=ob.matrix_world.copy()
    ob.parent=root
    ob.matrix_world=mx
    if ob.type=="CURVE":
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.convert(target="MESH")
        ob.select_set(False)

def light(loc,power,size):
    ld=bpy.data.lights.new("studio area","AREA")
    obj=bpy.data.objects.new("studio area",ld)
    bpy.context.collection.objects.link(obj)
    obj.location=loc
    ld.energy=power;ld.shape="DISK";ld.size=size
    obj.rotation_euler=(Vector((0,0,1.15))-obj.location).to_track_quat("-Z","Y").to_euler()
light((-3,-4,4),1450,5)
light((3,2,3),900,4)
sc=bpy.context.scene
sc.render.engine="CYCLES"
sc.cycles.samples=32
sc.render.resolution_x=1200
sc.render.resolution_y=1600
sc.render.resolution_percentage=100
sc.render.film_transparent=True
sc.view_settings.view_transform="AgX"
for name,pos in [
    ("front_orthographic",(0,-6,1.15)),
    ("three_quarter",(2.3,-5,1.7)),
    ("side_orthographic",(6,0,1.15)),
    ("rear_orthographic",(0,6,1.15)),
]:
    bpy.ops.object.camera_add(location=pos)
    cam=bpy.context.object
    cam.rotation_euler=(Vector((0,0,1.15))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=2.53
    sc.camera=cam;sc.render.filepath=str(OUT/(name+".png"))
    bpy.ops.render.render(write_still=True)

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
bpy.ops.export_scene.gltf(filepath=str(OUT/"Blacksmith_Door_Art_002.glb"),
    export_format="GLB",use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"Blacksmith_Door_Art_002.blend"))
with (OUT/"DESIGN_AUDIT.json").open("w") as f:
    json.dump({"source":"V002 rebuilt manifold arched iron leaf; repaired missing front right half",
        "legacy_meshes_reused":0,"shape":"arched_iron_merchant_shop",
        "true_circular_peep_hole":True,"lever_count":1,"wood":False,
        "texture_pixels":768,"texture_max_allowed":1536,
        "geometry_budget_target_triangles":25000,
        "note":"Not approved until real Blender render visual evaluation"},f,indent=2)
