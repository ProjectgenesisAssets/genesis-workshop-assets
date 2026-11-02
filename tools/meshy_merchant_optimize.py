import bpy, math, os, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# Keep every rendition based on the unmodified original, not on the previous decimation.
argv = sys.argv[sys.argv.index("--")+1:]
mode=argv[0]
source=argv[1]
out=argv[2]
os.makedirs(out,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=source)
objects=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert len(objects)==1, f"Expected 1 model mesh; got {len(objects)}"
original=objects[0]
original.name="Original_Merchant"
src_verts=len(original.data.vertices)
src_faces=sum(len(p.vertices)-2 for p in original.data.polygons)
corners=[original.matrix_world @ Vector(p) for p in original.bound_box]
mn=Vector([min(v[i] for v in corners) for i in range(3)])
mx=Vector([max(v[i] for v in corners) for i in range(3)])
center=(mn+mx)*.5
height=max(1e-9,mx.z-mn.z)
span=max(mx.x-mn.x,mx.y-mn.y,height)
print("SOURCE",src_verts,src_faces,"BBOX",tuple(mn),tuple(mx),flush=True)

def make_camera(angle_deg,elev=.14):
    angle=math.radians(angle_deg)
    cam=bpy.data.objects.get("MainCamera")
    if cam is None:
        bpy.ops.object.camera_add()
        cam=bpy.context.object
        cam.name="MainCamera"
    d=span*3.3
    cam.location=center+Vector((d*math.sin(angle), -d*math.cos(angle), d*elev))
    target=center+Vector((0,0,.06*height))
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO"
    cam.data.ortho_scale=span*1.48
    bpy.context.scene.camera=cam

def studio():
    world=bpy.data.worlds.new("Soft Studio World")
    bpy.context.scene.world=world
    world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.32,.38,.45,1)
    bg.inputs["Strength"].default_value=.7
    def area(name,pos,power,size):
        data=bpy.data.lights.new(name,"AREA")
        obj=bpy.data.objects.new(name,data)
        bpy.context.collection.objects.link(obj)
        obj.location=center+Vector((pos[0]*span,pos[1]*span,pos[2]*span))
        obj.rotation_euler=(center-obj.location).to_track_quat("-Z","Y").to_euler()
        data.energy=power
        data.shape="DISK"
        data.size=size*span
    area("Key softbox",(-1.5,-2,2.4),700,3)
    area("Fill softbox",(2,-.8,1),420,3)
    area("Rim softbox",(.5,2,2),850,2.2)
    s=bpy.context.scene
    s.render.engine="CYCLES"
    s.cycles.device="CPU"
    s.render.image_settings.file_format="PNG"
    s.render.image_settings.color_mode="RGBA"
    s.render.film_transparent=True
    s.render.resolution_percentage=100
    s.view_settings.view_transform="AgX" if hasattr(s.view_settings,"view_transform") else "Standard"
    s.render.image_settings.color_depth="8"
    s.render.threads_mode="FIXED"
    s.render.threads=4

def visible(obj):
    for mesh_obj in (o for o in bpy.context.scene.objects if o.type=="MESH"):
        mesh_obj.hide_render=(mesh_obj is not obj)

def decimate(ratio):
    obj=original.copy()
    obj.data=original.data.copy()
    bpy.context.collection.objects.link(obj)
    obj.matrix_world=original.matrix_world.copy()
    obj.name=f"Merchant_ratio_{ratio:.2f}"
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    mod=obj.modifiers.new("Conservative quadrics decimation","DECIMATE")
    mod.decimate_type="COLLAPSE"
    mod.ratio=ratio
    mod.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj

def shape_error(obj):
    # Deterministic sampled reference-to-optimized surface displacement.
    # This is geometry evidence in addition to multiview image comparisons.
    bvh=BVHTree.FromPolygons([v.co for v in obj.data.vertices],
       [list(p.vertices) for p in obj.data.polygons],all_triangles=False)
    step=max(1,len(original.data.vertices)//8000)
    diffs=[]
    for v in list(original.data.vertices)[::step]:
        point,normal,index,distance=bvh.find_nearest(v.co)
        if distance is not None: diffs.append(distance)
    diffs.sort()
    if not diffs:return {"sample_count":0,"max_height_percent":100,"p95_height_percent":100}
    # Local->world scale; same matrix for both. Character height in local-space.
    height_local=max(v.co.z for v in original.data.vertices)-min(v.co.z for v in original.data.vertices)
    # In case source orientation is not upright in object-local space, use largest dimension.
    local_extents=[max(v.co[i] for v in original.data.vertices)-min(v.co[i] for v in original.data.vertices) for i in range(3)]
    scale=max(local_extents)
    return {"sample_count":len(diffs),"max_height_percent":100*diffs[-1]/scale,
            "p95_height_percent":100*diffs[int((len(diffs)-1)*.95)]/scale,
            "mean_height_percent":100*sum(diffs)/len(diffs)/scale}

studio()
scene=bpy.context.scene
scene.render.resolution_x=380
scene.render.resolution_y=520
scene.cycles.samples=12
scene.render.image_settings.color_mode="RGBA"
if hasattr(scene.view_layers[0],"cycles"):
    scene.view_layers[0].cycles.use_denoising=False

def render_file(path,angle,samples=12,width=380,screen_height=520):
    make_camera(angle)
    scene.render.resolution_x=width
    scene.render.resolution_y=screen_height
    scene.cycles.samples=samples
    scene.render.filepath=path
    bpy.ops.render.render(write_still=True)
    print("RENDER",path,flush=True)

if mode=="candidates":
    visible(original)
    for angle in (0,90,180):
        render_file(f"{out}/original_{angle}.png",angle)
    info={"source_triangles":src_faces,"source_vertices":src_verts,"candidates":[]}
    for ratio in (.9,.8,.7,.6,.5,.4,.3,.25,.20,.16,.12,.10,.08,.06):
        o=decimate(ratio)
        tri=sum(len(p.vertices)-2 for p in o.data.polygons)
        stat=shape_error(o)
        record={"ratio":ratio,"triangles":tri,"vertices":len(o.data.vertices),**stat}
        print("CANDIDATE",json.dumps(record),flush=True)
        info["candidates"].append(record)
        visible(o)
        for angle in (0,90,180):
            render_file(f"{out}/r{ratio:.2f}_{angle}.png",angle)
        bpy.data.objects.remove(o,do_unlink=True)
        visible(original)
    with open(f"{out}/geometry_metrics.json","w") as f:json.dump(info,f,indent=2)
elif mode=="final":
    with open(f"{out}/selected.json") as f: selected=json.load(f)
    ratio=selected["ratio"]
    assert 0 < ratio <= 1
    o=decimate(ratio)
    tri=sum(len(p.vertices)-2 for p in o.data.polygons)
    visible(o)
    o.name="ProjectGenesis_Merchant_Optimized"
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.gltf(filepath=f"{out}/ProjectGenesis_Mercader_Optimizado.glb",
       export_format="GLB",use_selection=True,export_apply=False,export_texcoords=True,
       export_normals=True,export_materials="EXPORT")
    # Larger real Cycles preview: original and optimized under exactly same lighting.
    for label,ob in (("original",original),("optimized",o)):
        visible(ob)
        for angle in (0,45,90):
            render_file(f"{out}/final_{label}_{angle}.png",angle,samples=48,width=880,screen_height=1040)
    report={"ratio":ratio,"source_triangles":src_faces,"optimized_triangles":tri,
            "reduction_percent":100*(1-tri/src_faces),"materials":len(o.data.materials)}
    with open(f"{out}/final_metrics.json","w") as f:json.dump(report,f,indent=2)
    print("FINAL",json.dumps(report),flush=True)
else:
    raise ValueError(f"Unknown mode {mode}")
