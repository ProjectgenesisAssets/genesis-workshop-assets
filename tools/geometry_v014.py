"""V014 evaluation-driven realism: exposed radial wood fracture and baked end-grain,
irregular cured hide outline, connected natural hemp fibers. No autonomous approval."""
import math
from math import sin, cos, pi, exp
from mathutils import Quaternion, Vector
_v013_wood=wood_piece
_v013_hide=hide
_v013_cord=cord
_prev_endgrain=v4_endgrain_material
_endgrain_material_cache=None
def v4_endgrain_material():
    global _endgrain_material_cache
    if _endgrain_material_cache is not None:
        return _endgrain_material_cache
    # A real PBR bitmap is needed for WebGL; Blender's procedural wave node is not
    # faithfully exported to GLB. This is a generated end-cut reference texture, NOT a scan.
    import numpy as np
    size=768
    yy,xx=np.mgrid[0:size,0:size].astype(np.float32)
    px=(xx-size*.49)/(size*.50)
    py=(yy-size*.51)/(size*.50)
    r=np.sqrt(px*px + py*py)
    ang=np.arctan2(py,px)
    distorted=r+.018*np.sin(11*ang+7*r)+.013*np.sin(17*ang-3*r)
    rings=np.cos(2*pi*(distorted*(22 if K=="dry-oak-wood" else 28)+.5*np.sin(8*distorted)))
    pores=np.sin(70*px + 15*np.sin(8*py))*np.sin(38*py)
    rng=np.random.default_rng(253 if K=="dry-oak-wood" else 757)
    noise=rng.normal(0,.014,(size,size))
    variation=np.clip(.81+.12*rings+.032*pores+noise,.45,1.06)
    base=(.42,.275,.147) if K=="dry-oak-wood" else (.68,.51,.32)
    rgb=np.stack([np.clip(variation*c,0,1) for c in base],axis=-1)
    rgba=np.concatenate((rgb,np.ones((size,size,1),dtype=np.float32)),axis=2)
    image=bpy.data.images.new(K+"_cut_endgrain_V014",width=size,height=size,alpha=True)
    image.pixels.foreach_set(rgba.ravel().astype(np.float32))
    image.filepath_raw=str((out/(K+"_cut_endgrain_V014.png")).resolve())
    image.file_format="PNG"
    image.save()
    material=mat.copy()
    material.name=K+"_baked_endgrain_not_scan"
    n=material.node_tree.nodes
    shader=n.get("Principled BSDF")
    tex=n.new("ShaderNodeTexImage")
    tex.image=image
    material.node_tree.links.new(tex.outputs["Color"],shader.inputs["Base Color"])
    _endgrain_material_cache=material
    return material
def wood_piece(label,oak,offset):
    ob=_v013_wood(label,oak,offset)
    # Rotate around the log's OWN longitudinal axis. This exposes torn raw wood while
    # preserving its horizontal pile direction, unlike the old Euler-X rotation.
    original=ob.rotation_euler.to_quaternion()
    spin=Quaternion((0,0,1),(2.25 if oak else 2.03)+offset*.13)
    rotation=original @ spin
    ob.rotation_mode="QUATERNION"
    ob.rotation_quaternion=rotation
    for child in objects:
        if child.name.startswith(label+"_grain_sliver"):
            child.rotation_mode="QUATERNION"
            child.rotation_quaternion=rotation.copy()
    return ob
def hide(cow):
    begin=len(objects)
    item=_v013_hide(cow)
    # Break rectangle outlines without introducing unrealistic giant corner spikes.
    for ob in objects[begin:]:
        if "_natural_fold_" not in ob.name:continue
        nx=43;ny=38
        count=nx*ny
        for idx,v in enumerate(ob.data.vertices):
            t=idx%count
            xix=t%nx; yix=t//nx
            u=xix/(nx-1); w=yix/(ny-1)
            x,y,z=v.co
            edgeu=(abs(2*u-1))**6
            edgev=(abs(2*w-1))**6
            x+=(.031 if cow else .045)*edgeu*sin(10*w+2.3*u)
            y+=(.022 if cow else .047)*edgev*sin(9*u+3.1*w)
            # Tightening near two stress directions yields a physically plausible drape.
            z+=(.009 if cow else .016)*sin(14*u+3*w)*exp(-((w-.24)/.15)**2)
            v.co=(x,y,z)
        ob.data.update()
    return item
def cord(hemp):
    item=_v013_cord(hemp)
    if not hemp:
        return item
    # Frays originate from ACTUAL final strand vertices, not guessed coordinates.
    for ob in list(objects):
        if "natural_hemp_three_strand_coil" not in ob.name:continue
        me=ob.data
        steps=460; sides=7
        for part in range(3):
            base=(part*steps+steps-1)*sides
            for k in range(4):
                vertex=me.vertices[base+(k*2)%sides].co.copy()
                prev=me.vertices[base-sides+(k*2)%sides].co.copy()
                direction=(vertex-prev).normalized()
                lateral=Vector((-direction.y,direction.x,.15))
                L=.014+.008*k
                e=vertex+direction*L+lateral*(.009+.002*k)
                f=vertex+direction*(L*.94)+lateral*(.009+.002*k)+Vector((.001,.001,.001))
                mesh("connected_hemp_tip_%d_%d"%(part,k),
                     [tuple(vertex),tuple(e),tuple(f)],[(0,1,2)],mats=[mat])
    return item
