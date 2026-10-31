# Project Genesis  |  Six Level-1 Tutorial Materials  |  Blender 4.5.13 LTS
# Artist-built silhouette and plausible fracture anatomy; photographed Poly Haven CC0 PBR surface maps.
# All generated models are REVIEW CANDIDATES, never automatically integrated into PlayCanvas.
import bpy,sys,math,json,random,hashlib
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi

slug=sys.argv[sys.argv.index('--')+1]
config=json.loads(Path(f'production/tutorial_materials/config/{slug}.json').read_text())
out=Path(f'production/tutorial_materials/generated/{slug}')
src=out/'source'
out.mkdir(parents=True,exist_ok=True)
seed=int(hashlib.sha256(slug.encode()).hexdigest()[:8],16)
rnd=random.Random(seed)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def node_image(path,space):
    im=bpy.data.images.load(str(path.resolve()),check_existing=True)
    im.colorspace_settings.name=space
    return im
def make_pbr(role,name,tint=(1,1,1),roughness_scale=1.0):
    base=src/(role+'_albedo.jpg')
    norm=src/(role+'_normal.png')
    rough=src/(role+'_roughness.png')
    for file in (base,norm,rough):
        if not file.is_file():raise RuntimeError('Missing real scan PBR '+str(file))
    material=bpy.data.materials.new(name)
    material.use_nodes=True;material.diffuse_color=(*tint,1)
    nodes=material.node_tree.nodes;links=material.node_tree.links;nodes.clear()
    output=nodes.new('ShaderNodeOutputMaterial');output.location=(670,120)
    p=nodes.new('ShaderNodeBsdfPrincipled');p.location=(380,120)
    p.inputs['Metallic'].default_value=0
    p.inputs['IOR'].default_value=1.47 if config['kind']=='leather' else 1.45
    p.inputs['Roughness'].default_value=.85
    links.new(p.outputs['BSDF'],output.inputs['Surface'])
    tex=nodes.new('ShaderNodeTexImage');tex.image=node_image(base,'sRGB');tex.location=(-540,370)
    if tint!=(1,1,1):
        mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1.0
        mix.inputs[2].default_value=(*tint,1)
        links.new(tex.outputs['Color'],mix.inputs[1])
        links.new(mix.outputs[0],p.inputs['Base Color'])
    else: links.new(tex.outputs['Color'],p.inputs['Base Color'])
    texr=nodes.new('ShaderNodeTexImage');texr.image=node_image(rough,'Non-Color');texr.location=(-540,-30)
    if roughness_scale!=1:
        mult=nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=roughness_scale
        links.new(texr.outputs['Color'],mult.inputs[0]);links.new(mult.outputs[0],p.inputs['Roughness'])
    else:links.new(texr.outputs['Color'],p.inputs['Roughness'])
    texn=nodes.new('ShaderNodeTexImage');texn.image=node_image(norm,'Non-Color');texn.location=(-540,-290)
    nnode=nodes.new('ShaderNodeNormalMap');nnode.space='TANGENT';nnode.inputs['Strength'].default_value=.88
    links.new(texn.outputs['Color'],nnode.inputs['Color']);links.new(nnode.outputs[0],p.inputs['Normal'])
    return material

def mesh_from_faces(name,verts,faces,uvs,mats,ids=None,smooth=True):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    if any(not math.isfinite(c) for v in verts for c in v): raise RuntimeError('NaN in artist model')
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    for m in mats:mesh.materials.append(m)
    uv=mesh.uv_layers.new(name='PhysicallyMappedUV')
    for i,poly in enumerate(mesh.polygons):
        if ids:poly.material_index=ids[i]
        for li in poly.loop_indices:uv.data[li].uv=uvs[i][li-poly.loop_start]
        poly.use_smooth=smooth
    return ob

def make_log(species):
    oak=species=='roble'
    wood=make_pbr('wood','Real CC0 hardwood scanned grain | '+species,
                  tint=(.81,.68,.53) if oak else (.96,.94,.83),roughness_scale=1.1)
    bark=make_pbr('bark','Real CC0 bark furrows | '+species,
                  tint=(.57,.46,.36) if oak else (.69,.70,.66))
    # Section of an actual split firewood log: convex bark arc and two broken radial fibre planes.
    # Physically consistent longitudinal fractures, incomplete rings, uneven saw-cut ends.
    L=.46 if oak else .49
    radius=.113 if oak else .102
    steps=44;length_steps=21
    theta0=-1.08 if oak else -1.14
    theta1=1.06 if oak else 1.10
    verts=[];faces=[];uv=[];ids=[]
    def addface(v,uvv,m):
        faces.append(v);uv.append(uvv);ids.append(m)
    def newv(p):verts.append(tuple(p));return len(verts)-1
    # Bark outside: displaced ridges correspond to actual growth direction (Z).
    grid=[]
    for j in range(length_steps+1):
        t=j/length_steps;z=L*(t-.5)
        row=[]
        for i in range(steps+1):
            u=i/steps;angle=theta0+(theta1-theta0)*u
            axial=.0023*sin(z*78+u*13.2)+.0012*sin(z*191+u*28.4)
            radial=radius+axial+(.0031 if oak else .0017)*sin(u*13*pi+z*4)
            radial+=.0017*sin(u*49+z*5)
            z_jitter=.0011*sin(angle*9+z*26)
            row.append(newv((radial*cos(angle),radial*sin(angle),z+z_jitter)))
        grid.append(row)
    for j in range(length_steps):
        for i in range(steps):
            a,b,c,d=grid[j][i],grid[j][i+1],grid[j+1][i+1],grid[j+1][i]
            addface((a,b,c,d),((i/steps*2,j/length_steps*1.4),((i+1)/steps*2,j/length_steps*1.4),((i+1)/steps*2,(j+1)/length_steps*1.4),(i/steps*2,(j+1)/length_steps*1.4)),1)
    # Two split radial faces with irregular raised fibres and winding deep grain clefts.
    for wall,theta in enumerate((theta0,theta1)):
        grid=[]
        for j in range(length_steps+1):
            z=L*(j/length_steps-.5);row=[]
            for k in range(18):
                r=radius*k/17
                # Fibres follow log axis: two deep axial checks, only tiny lateral meander.
                t=k/17
                check=0.0033*math.exp(-((t-(.29+.034*sin(z*19))) / .043)**2)
                check+=0.0021*math.exp(-((t-(.71+.020*sin(z*17))) / .055)**2)
                depth=.0015*sin(z*97+r*210)+.0009*sin(z*223+r*410)-check
                theta_j=theta+(depth/radius)*(1 if wall==0 else -1)
                rr=max(.001,r+.00075*sin(z*37+r*55))
                row.append(newv((rr*cos(theta_j),rr*sin(theta_j),z+.0011*sin(z*49+r*100))))
            grid.append(row)
        for j in range(length_steps):
            for k in range(17):
                a,b,c,d=grid[j][k],grid[j][k+1],grid[j+1][k+1],grid[j+1][k]
                f=(a,b,c,d) if wall==0 else (d,c,b,a)
                addface(f,((k/17*1.4,j/length_steps*1.8),((k+1)/17*1.4,j/length_steps*1.8),((k+1)/17*1.4,(j+1)/length_steps*1.8),(k/17*1.4,(j+1)/length_steps*1.8)),0)
    # Cross-grain end sections. Radial growth ring grooves etched into real geometry,
    # with two splits following the grain; no arbitrary floating crack lines.
    for sign in (-1,1):
        rings=16; grid=[]
        for ri in range(rings+1):
            r=radius*ri/rings;row=[]
            for a in range(steps+1):
                angle=theta0+(theta1-theta0)*a/steps
                ring=.0014*sin(2*pi*(ri/2.85)+.37*sin(angle*3.0))
                checks=.0030*math.exp(-((angle-(-.17+.04*sin(ri*.4)))/.033)**2)
                checks+=.0020*math.exp(-((angle-(.61+.03*sin(ri*.4)))/.027)**2)
                z=sign*L*.5+sign*(ring-checks)*min(1,r/.04)
                row.append(newv((r*cos(angle),r*sin(angle),z)))
            grid.append(row)
        for ri in range(rings):
            for a in range(steps):
                aa,bb,cc,dd=grid[ri][a],grid[ri][a+1],grid[ri+1][a+1],grid[ri+1][a]
                f=(aa,bb,cc,dd) if sign==1 else (dd,cc,bb,aa)
                addface(f,((.5+.5*ri/rings*cos(theta0+(theta1-theta0)*a/steps),.5+.5*ri/rings*sin(theta0+(theta1-theta0)*a/steps)),
                            (.5+.5*ri/rings*cos(theta0+(theta1-theta0)*(a+1)/steps),.5+.5*ri/rings*sin(theta0+(theta1-theta0)*(a+1)/steps)),
                            (.5+.5*(ri+1)/rings*cos(theta0+(theta1-theta0)*(a+1)/steps),.5+.5*(ri+1)/rings*sin(theta0+(theta1-theta0)*(a+1)/steps)),
                            (.5+.5*(ri+1)/rings*cos(theta0+(theta1-theta0)*a/steps),.5+.5*(ri+1)/rings*sin(theta0+(theta1-theta0)*a/steps))),0)
    ob=mesh_from_faces('Split seasoned '+species+' - continuous bark / fibre / endgrain',verts,faces,uv,[wood,bark],ids)
    # Put the log in a physical resting diagonal orientation for the inventory, without distorting geometry.
    ob.rotation_euler=(math.radians(71),math.radians(-17 if oak else 14),math.radians(-27 if oak else 22))
    ob.location=(0,0,.125)
    return [ob]

def make_hide(animal):
    cow=animal=='bovino'
    m=make_pbr('leather','Scanned tanned hide | '+animal,
               tint=(.66,.47,.29) if cow else (.80,.66,.47),
               roughness_scale=1.20 if cow else 1.05)
    # Hand-cut organically irregular cured-hide border; varied thickness and sparse tensile folds.
    nu=68;nv=42
    half_x=.285 if cow else .234
    half_y=.19 if cow else .156
    verts=[];faces=[];uvs=[]
    for iy in range(nv+1):
        v=iy/nv;row=[]
        for ix in range(nu+1):
            u=ix/nu
            x=(u-.5)*2*half_x
            y=(v-.5)*2*half_y
            edgeu=(abs(2*u-1)**8)
            edgev=(abs(2*v-1)**8)
            x+=half_x*.07*math.sin(v*7.1+1.1)*edgeu
            y+=half_y*.065*math.sin(u*9.7+.2)*edgev
            # Two coherent folds with pressure direction: broad main drape and narrower buckle.
            main=.044*math.exp(-((u-(.30+.12*math.sin(2*pi*v)))/.12)**2)
            buckle=.026*math.exp(-((v-(.70+.07*math.sin(3*pi*u)))/.066)**2)
            drape=.014*math.sin(u*2*pi+.3)*math.cos(v*2*pi)
            curl=.051*max(0,(u-.78)/.22)**2
            z=.028+main+buckle+drape+curl+.0011*math.sin(25*u+14*v)
            verts.append((x,y,z))
    for iy in range(nv):
        for ix in range(nu):
            a=iy*(nu+1)+ix;b=a+1;c=b+(nu+1);d=a+(nu+1)
            faces.append((a,b,c,d))
            # Fine bovine grain vs smaller tighter caprine grain: two different UV scales.
            scale=1.35 if cow else 2.25
            u0=ix/nu*scale;u1=(ix+1)/nu*scale;v0=iy/nv*scale;v1=(iy+1)/nv*scale
            uvs.append(((u0,v0),(u1,v0),(u1,v1),(u0,v1)))
    ob=mesh_from_faces('Vegetable tanned '+animal+' naturally folded hide',verts,faces,uvs,[m])
    solid=ob.modifiers.new('Real physical cut leather thickness','SOLIDIFY')
    solid.thickness=.0035 if cow else .0020
    solid.offset=-1
    solid.use_rim=True
    sub=ob.modifiers.new('Gentle tangential smooth drape','SUBSURF');sub.levels=1;sub.render_levels=1
    # Keep clean irregular outline, do not fake wool, stitches, rivets or fabric embossing.
    ob.rotation_euler=(math.radians(18),math.radians(-6),math.radians(-16 if cow else 18))
    ob.location=(0,0,.014)
    return [ob]

def make_tube(name,coords,radius,material,segments=8,texture_repeat=1):
    coords=[Vector(c) for c in coords]
    vert=[];uv=[];faces=[]
    for i,center in enumerate(coords):
        tangent=(coords[min(i+1,len(coords)-1)]-coords[max(i-1,0)]).normalized()
        if tangent.length<.01:tangent=Vector((0,0,1))
        ref=Vector((0,0,1)) if abs(tangent.z)<.94 else Vector((0,1,0))
        a=tangent.cross(ref).normalized();b=tangent.cross(a).normalized()
        for j in range(segments):
            ang=2*pi*j/segments
            rr=radius*(1+.08*sin(i*.37+j*2.9))
            pt=center+rr*(a*cos(ang)+b*sin(ang))
            vert.append(tuple(pt))
    for i in range(len(coords)-1):
        for j in range(segments):
            a=i*segments+j;b=i*segments+(j+1)%segments
            c=(i+1)*segments+(j+1)%segments;d=(i+1)*segments+j
            faces.append((a,b,c,d))
            uv.append(((j/segments,i/(len(coords)-1)*texture_repeat),
                       ((j+1)/segments,i/(len(coords)-1)*texture_repeat),
                       ((j+1)/segments,(i+1)/(len(coords)-1)*texture_repeat),
                       (j/segments,(i+1)/(len(coords)-1)*texture_repeat)))
    return mesh_from_faces(name,vert,faces,uv,[material])

def make_fibre(kind):
    hemp=kind=='canamo'
    pbr=make_pbr('fiber','Photographed spun fibre '+kind,
                 tint=(.70,.60,.39) if hemp else (.89,.83,.68),roughness_scale=1.23)
    # Hemp: loose 3-strand plied cord coil with coherent counter-twisting and a free end.
    # Linen: narrower twin-ply yarn skein (multiple elongated turns, not a rope recolor).
    strands=3 if hemp else 2
    copies=1 if hemp else 6
    created=[]
    for copy in range(copies):
        coords=[]
        n=480 if hemp else 270
        for i in range(n):
            t=i/(n-1)
            if hemp:
                turns=3.18
                theta=t*turns*2*pi
                R=.065+.026*t
                x=R*cos(theta);y=R*sin(theta)
                z=.032+.007*t+.004*sin(theta*2)
                if t>.92:
                    s=(t-.92)/.08
                    x+=.055*s;y-=.035*s;z+=.018*s
            else:
                theta=t*2*pi*2.1
                # Elongated skein wrap; stagger each winding without changing fibre diameter.
                x=.095*cos(theta)+copy*.0022
                y=.022*sin(theta)+(.0027*(copy-2.5))
                z=.027+copy*.0018+.004*sin(theta*3)
            coords.append(Vector((x,y,z)))
        total_distance=sum((coords[i]-coords[i-1]).length for i in range(1,len(coords)))
        cumulative=[0.]
        for i in range(1,len(coords)):cumulative.append(cumulative[-1]+(coords[i]-coords[i-1]).length)
        strand_r=.0047 if hemp else .0019
        for strand in range(strands):
            path=[]
            for i,pos in enumerate(coords):
                tangent=(coords[min(i+1,n-1)]-coords[max(0,i-1)]).normalized()
                axis=(Vector((0,0,1))-tangent*tangent.z).normalized()
                if axis.length<.2:axis=Vector((1,0,0))
                side=tangent.cross(axis).normalized()
                # A true helical ply around the *moving* path, not a painted stripe.
                phi=2*pi*(cumulative[i]/(.038 if hemp else .012)+strand/strands)
                off=axis*cos(phi)+side*sin(phi)
                path.append(pos+off*(.0050 if hemp else .00195))
            created.append(make_tube(f'{kind} | coil {copy+1} | twisted ply {strand+1}',path,
                    strand_r,pbr,segments=7 if hemp else 6,texture_repeat=5 if hemp else 8))
    # A few mechanically plausible loose fly-away fibres at the free end, without fuzzy halo.
    for i in range(15 if hemp else 10):
        base=Vector((.11,-.03,.065)) if hemp else Vector((.09,0,.035))
        a=(i*2.399963)% (2*pi)
        delta=Vector((cos(a)*(.013+rnd.random()*.016),sin(a)*(.01+rnd.random()*.01),rnd.random()*.018))
        created.append(make_tube(f'{kind} isolated split fibril {i+1}',[base,base+delta],
                    .00045 if hemp else .00025,pbr,segments=4))
    return created

def visible_bounds(objects):
    bpy.context.view_layer.update()
    p=[o.matrix_world@Vector(c) for o in objects if o.type=='MESH' for c in o.bound_box]
    return (Vector([(min(v[i] for v in p)+max(v[i] for v in p))/2 for i in range(3)]),
            max(max(v[i] for v in p)-min(v[i] for v in p) for i in range(3)))
kind=config['kind']
if kind=='wood': models=make_log(config['species'])
elif kind=='leather':models=make_hide(config['animal'])
elif kind=='fiber':models=make_fibre(config['fiber'])
else:raise ValueError('Unknown kind '+kind)

# Resolve and pack all real CC0 source textures before saving / changing .blend working directory.\nbpy.ops.file.pack_all()\n# Export exactly the intended material, no camera or lights.
bpy.ops.object.select_all(action='DESELECT')
for o in models:o.select_set(True)
bpy.context.view_layer.objects.active=models[0]
path=out/f'{slug}_{config["version"].lower()}_candidate.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
                          export_apply=True,export_image_format='AUTO',export_materials='EXPORT')
if path.stat().st_size<18000: raise RuntimeError('Empty GLB')
# Save the working Blender scene for full manual artist refinement.
bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{slug}_{config["version"].lower()}_master.blend'))

# All views share exactly the same light and neutral color management.
world=bpy.data.worlds.new('Neutral 3D scan review studio');bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.34,.35,.37,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55
center,size=visible_bounds(models)
def area(name,pos,energy,diameter):
    light=bpy.data.lights.new(name,'AREA');light.energy=energy;light.shape='DISK';light.size=diameter
    ob=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(ob)
    ob.location=center+Vector(pos);ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
area('Large front key - natural neutral', (1.5,-1.5,2.3),550,3.2)
area('Wide fill shows fractures',(-1.8,-.9,.8),330,2.5)
area('Rim separates fibre contours',(-.9,1.6,1.8),480,2.1)
cam_data=bpy.data.cameras.new('Orthographic art evaluation')
cam_data.type='ORTHO'
cam=bpy.data.objects.new('Orthographic art evaluation',cam_data);bpy.context.collection.objects.link(cam)
scene=bpy.context.scene;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=28;scene.cycles.use_denoising=True
scene.render.resolution_x=860;scene.render.resolution_y=860;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.15
views={
 'hero':(1.6,-2.3,1.5),
 'side':(2.2,.4,.65),
 'top':(.25,-.4,2.8),
 'back':(-1.65,2.25,1.3),
 'macro':(1.0,-2.0,1.25)
}
for name,off in views.items():
    cam.location=center+Vector(off);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    cam_data.ortho_scale=max(.24,size*(1.57 if name!='macro' else 1.21))
    scene.render.filepath=str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
scene.render.resolution_x=640;scene.render.resolution_y=640
scene.render.filepath=str(out/'inventory_poster_rgba.png')
cam.location=center+Vector(views['hero'])
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.ortho_scale=max(.24,size*1.56)
bpy.ops.render.render(write_still=True)
print('SIX_MATERIALS_BLENDER_GENERATED',slug,'objects',len(models),'GLB_bytes',path.stat().st_size)
