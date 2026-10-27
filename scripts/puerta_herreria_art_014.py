# Door V011: real rear hinge-side reinforcement connections and legible metal QA.
# Blender 4.5 / PlayCanvas GLB; all scene generation runs in GitHub Actions.
import bpy, math, json, random
from math import sin, cos, pi
from pathlib import Path
from mathutils import Vector
import numpy as np

OUT=Path("output_blacksmith_door_art_014")
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
    n=2048  # 2K exploratory PBR for aged iron; optimizable after visual approval
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
    broad=smooth_noise(26)
    fine=smooth_noise(96)
    micro=rng.normal(0,1,(n,n)).astype(np.float32)
    cloud=np.clip(broad*.72+fine*.26,-1.8,1.8)
    scratches=np.clip(smooth_noise(240)*.12+micro*.09,-.16,.16)
    # V013: preserve largely blue-black wrought iron; oxidation lives in low-exposure
    # material groups and irregular recessed patches, not as a continuous brown paint.
    # Each channel is physically consistent: iron metallic, ferric patina rough/nonmetal.
    broad_oxide=smooth_noise(11)
    weather=np.clip(.68*broad+.30*broad_oxide+.21*fine,-2.2,2.2)
    oxide_seed=np.maximum(0.0, weather-.16)
    if "brass" in name:
        oxide=np.zeros_like(oxide_seed)
        ageing=.016
    elif "inset" in name:
        oxide=np.clip(.58*oxide_seed+.038*np.maximum(0,broad_oxide),0,.53)
        ageing=.064
    elif "highlights" in name:
        oxide=np.clip(.12*oxide_seed,0,.13)
        ageing=.009
    else:
        oxide=np.clip(.39*oxide_seed+.021*np.maximum(0,broad_oxide),0,.41)
        ageing=.019
    variation=np.clip(1+.085*broad+.036*fine+.045*scratches,.78,1.17)
    # Subtle graphite/blue steel, visible only as specular texture variation.
    axis=np.linspace(0,1,n,dtype=np.float32)
    xx=axis[:,None];yy=axis[None,:]
    edge_distance=np.minimum(np.minimum(xx,1-xx),np.minimum(yy,1-yy))
    worn=np.exp(-edge_distance/.028)*(.26+.12*np.maximum(-cloud,0))
    rust_color=(.365,.117,.050)
    color=np.stack([np.clip(
        base[k]*variation*(1-ageing)*(1-.035*worn)
        + oxide*(rust_color[k]-base[k])
        + worn*(.024 if k==0 else (.029 if k==1 else .033)),
        0,1) for k in range(3)],axis=-1)
    rough=np.clip(
        roughness+.031*fine+.013*micro+.37*oxide+
        .039*np.maximum(0.0,-weather),.31,.88)
    metalness=np.clip(metallic*(1-2.45*oxide),.10,1.0)
    # Local pitting belongs mainly to oxide; the surrounding forged metal stays fine.
    bump=np.clip(.50+.048*cloud+.023*fine+.014*micro+
                 .061*oxide*(.40+fine),0,1)
    nx=-np.gradient(bump,axis=1)*1.72
    ny=-np.gradient(bump,axis=0)*1.72
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
    met=map_img("metallic",np.repeat(metalness[:,:,None],3,axis=2),True)
    nodes=m.node_tree.nodes
    cl=nodes.new("ShaderNodeTexImage");cl.image=c
    rl=nodes.new("ShaderNodeTexImage");rl.image=r
    nl=nodes.new("ShaderNodeTexImage");nl.image=b
    ml=nodes.new("ShaderNodeTexImage");ml.image=met
    nm=nodes.new("ShaderNodeNormalMap");nm.inputs["Strength"].default_value=.38
    links=m.node_tree.links
    links.new(cl.outputs["Color"],bs.inputs["Base Color"])
    links.new(rl.outputs["Color"],bs.inputs["Roughness"])
    links.new(ml.outputs["Color"],bs.inputs["Metallic"])
    links.new(nl.outputs["Color"],nm.inputs["Color"])
    links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    return m

iron=material("iron_aged_blued_steel_v013",(.142,.150,.158),.94,.54,17)
edge=material("iron_worn_polished_edges_v013",(.195,.198,.199),.94,.45,18)
copper=material("copper_brass",(.268,.184,.100),.78,.60,19)
shade=material("iron_ferric_patina_insets_v013",(.087,.090,.094),.86,.66,20)
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
sc.cycles.samples=64
bpy.context.view_layer.cycles.use_denoising=True
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
bpy.ops.export_scene.gltf(filepath=str(OUT/"Blacksmith_Door_Art_014.glb"),
    export_format="GLB",use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"Blacksmith_Door_Art_014.blend"))
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
    json.dump({"source":"V012 material-only preview: V011 approved geometry preserved; oxidized iron proxy, not exact private V175 shader",
        "version":"V014","baseline_version":"V010",
        "targeted_repairs":["preserve connected rear structural braces and peephole through-mesh",
                            "reduce tiny rivet cylinders and curve tessellation below silhouette threshold",
                            "reduce hidden hammer plate subdivisions without removing PBR relief",
                            "reduce bevel segments and retain edge catchlights for front and side views"],
        "legacy_meshes_reused":0,"shape":"arched_iron_merchant_shop",
        "true_circular_peep_hole":True,"lever_count":1,"wood":False,
        "texture_pixels":2048,"texture_max_allowed":2048,
        "geometry_budget_target_triangles":25000,"evaluated_triangles":triangles,
        "budget_met":triangles<=25000,
        "note":"Budget is a target, not an automatic art approval; compare silhouette in four views"},f,indent=2)

with (OUT/"V014_MATERIAL_TEST.json").open("w",encoding="utf-8") as f:
    json.dump({"version":"V014","geometry_baseline":"V011_USER_APPROVED",
      "material_goal":"blue-black wrought iron with localized ferric oxide, inspired by approved ingot V175",
      "source_texture_copied":False,
      "exact_V175_material_applied":False,
      "reason":"V175 original lives in private repository; public preview deliberately uses independently generated proxy",
      "material_only":True,"artist_approval":"PENDING"},f,indent=2)
