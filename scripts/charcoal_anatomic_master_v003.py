# Project Genesis — CARBON VEGETAL HERO V003 | anatomical sculpt / real PBR
# Original geometry and texture study, based on CC0 scans and published wood anatomy.
# Keeps all previous versions intact. Blender 4.5.13 LTS / PlayCanvas candidate ONLY.
import bpy, math, random, json, os
from pathlib import Path
import numpy as np
from mathutils import Vector

SEED = 31102026
rng = random.Random(SEED)
np.random.seed(31026)
OUT = Path("output_charcoal_v003").resolve()
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def make_maps(label, side=True, res=1536):
    # True image-based PBR: baked bitmap textures survive glTF export.
    yy,xx = np.mgrid[0:res,0:res].astype(np.float32)
    u=xx/res; v=yy/res
    n1=np.sin(u*163.0+1.8*np.sin(v*9.5)+0.44*np.sin(v*34.0))
    n2=np.sin(u*371.0+0.9*np.sin(v*14.0)+np.sin(u*29.0+v*3.0))
    n3=np.sin(u*67.0+np.sin(v*7.0)*2.1)
    if side:
        # Annual wood fibres: longitudinal in UV; fine transverse checking.
        stria=0.45*n1+0.24*n2+0.31*n3
        wide=np.abs(np.sin(u*78+1.0*np.sin(v*7.7)+.3*np.sin(v*22)))
        long_split=np.exp(-((wide)/0.080)**2)*(0.60+0.40*np.sin(v*26+u*3)**2)
        cross_split=np.exp(-((np.abs(np.sin(v*79+1.4*np.sin(u*29))))/.043)**2)*0.35
        ridges=np.maximum(0,np.sin(u*230+v*0.7))**9
        height=0.14*stria-0.55*long_split-0.18*cross_split+0.06*ridges
    else:
        # End grain: annular growth layers, radial rays, cellular grain.
        cx=(u-.5)/.45; cy=(v-.5)/.45
        rr=np.sqrt(cx*cx+(cy*0.91)**2)
        a=np.arctan2(cy,cx)
        rings=np.sin(180*rr+2.7*np.sin(a*5)+1.0*np.sin(a*17))
        pores=np.sin(u*800)*np.sin(v*720)
        ray=np.exp(-((np.abs(np.sin(a*12.0+1.7*rr)))/.060)**2)
        height=0.18*rings+0.075*pores-0.29*ray
        stria=.61*rings+.24*pores+.15*np.sin(a*60)
        long_split=ray
        cross_split=np.maximum(0,np.sin(a*83+rr*45))**14*.13
    micro=np.sin(u*1281+v*71)*np.sin(v*963-u*31)
    height += .038*micro
    ash=np.maximum(0,np.sin(u*31.0+v*19.0)*np.cos(v*39.0-u*7))**10
    shade=np.clip(.124+.045*stria-.068*long_split-.024*cross_split+.020*ash, .018,.235)
    color=np.zeros((res,res,4),dtype=np.float32)
    color[:,:,0]=np.clip(shade*.92,0,1)
    color[:,:,1]=np.clip(shade*.95,0,1)
    color[:,:,2]=np.clip(shade*1.02,0,1)
    color[:,:,3]=1
    rough=np.clip(.82+.073*stria+.075*long_split-.08*ash,.68,.97)
    # Tangent-space OpenGL normal map from physically oriented height detail.
    dy,dx=np.gradient(height)
    normal=np.stack((-dx*.75,-dy*.75,np.ones_like(dx)*.72),axis=2)
    normal/=np.maximum(np.linalg.norm(normal,axis=2,keepdims=True),1e-5)
    normal=(normal*.5+.5)
    roughim=np.repeat(rough[:,:,None],3,axis=2)
    normalim=np.concatenate((normal,np.ones((res,res,1),dtype=np.float32)),axis=2)
    roughim=np.concatenate((roughim,np.ones((res,res,1),dtype=np.float32)),axis=2)
    def img(name, rgba, noncolor=False):
        im=bpy.data.images.new(name,width=res,height=res,alpha=True,float_buffer=False)
        im.pixels.foreach_set(np.flipud(rgba).reshape(-1))
        im.filepath_raw=str(OUT/(name+'.png'))
        im.file_format='PNG'
        im.save()
        if noncolor: im.colorspace_settings.name='Non-Color'
        im.pack()
        return im
    return img(label+'_basecolor',color), img(label+'_normal',normalim,True), img(label+'_roughness',roughim,True)

def material(name,maps):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes; nodes.clear()
    bs=nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Metallic'].default_value=0.0
    out=nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    tex=nodes.new('ShaderNodeTexImage');tex.image=maps[0]
    mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    texn=nodes.new('ShaderNodeTexImage');texn.image=maps[1]
    nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.82
    mat.node_tree.links.new(texn.outputs['Color'],nm.inputs['Color'])
    mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    texr=nodes.new('ShaderNodeTexImage');texr.image=maps[2]
    mat.node_tree.links.new(texr.outputs['Color'],bs.inputs['Roughness'])
    return mat

side_mat=material('CarbonizedHardwood_AxialFibres_PBR1536',make_maps('axial',True))
end_mat=material('CarbonizedHardwood_EndGrain_PBR1536',make_maps('endgrain',False))
root=bpy.data.objects.new('PG_Charcoal_Hero_V003_ROOT',None)
bpy.context.collection.objects.link(root)
root.rotation_euler=(math.radians(13),math.radians(22),math.radians(-18))
objects=[]

def build_sector(index,start,stop):
    # Each sector is a physical radial wedge. The fracture propagates
    # along the wood axis instead of appearing as random mineral facets.
    Nv=92
    Na=max(12,round((stop-start)*78/(math.pi*2)))
    Nr=19
    section_width=stop-start
    length=1.98 + rng.uniform(-.21,.19)
    phase=rng.uniform(0,6.28)
    radius_factor=rng.uniform(.89,1.02)
    vertices=[];faces=[]; UV=[]; mats=[]
    def vertex(pos):
        vertices.append(tuple(pos))
        return len(vertices)-1
    def quad(verts,uv,mat=0):
        faces.append(tuple(verts));UV.append(list(uv));mats.append(mat)
    def theta_bound(t,z):
        # Radial fissure width changes smoothly along its length.
        t=max(0,min(1,t))
        fissure=.014+.008*(.5+.5*math.sin(z*5.6+phase))
        return start+fissure+(section_width-2*fissure)*t
    def z_edge(t,side,rad=1):
        angle=start+section_width*t
        chip=.046*math.sin(angle*7.1+phase)+.034*math.sin(angle*17.9-phase)
        splinter=.055*(max(0,math.sin(angle*23.5+phase))**6)
        return side*(length*.5+chip+splinter*(.5+.5*rad))
    def radius(angle,z):
        broad=.072*math.sin(angle*3.0+.3*math.sin(z*2.2))
        broad+=.039*math.sin(angle*7.0+z*.38)
        axial=.016*math.sin(angle*37+1.2*math.sin(z*5+angle))
        axial+=.012*math.sin(angle*91+1.7*math.sin(z*2.6+phase))
        short=.018*math.sin(z*6.2+phase)*math.sin(angle*12.1+phase)
        breakaway=.071*max(0,math.sin(z*3.1+phase)*math.sin(angle*11.2+phase))**11
        return .59*radius_factor*(1+broad+axial+short-breakaway)
    def xyz(t,z,rad=1):
        theta=theta_bound(t,z)
        r=(.075+(.925)*rad)*radius(theta,z)
        return (r*math.cos(theta)*1.02,r*math.sin(theta)*.87,z)
    # Shell / longitudinal growth structure; sides of open cracks are real mesh.
    surf=[]
    for iz in range(Nv+1):
        v=iz/Nv
        row=[]
        for ia in range(Na+1):
            t=ia/Na
            z=(1-v)*z_edge(t,-1)+v*z_edge(t,1)
            row.append(vertex(xyz(t,z,1)))
        surf.append(row)
    for iz in range(Nv):
        for ia in range(Na):
            ids=(surf[iz][ia],surf[iz][ia+1],surf[iz+1][ia+1],surf[iz+1][ia])
            t0=ia/Na;t1=(ia+1)/Na
            v0=iz/Nv;v1=(iz+1)/Nv
            quad(ids,[(start/(2*math.pi)+section_width*t0/(2*math.pi),v0),
                      (start/(2*math.pi)+section_width*t1/(2*math.pi),v0),
                      (start/(2*math.pi)+section_width*t1/(2*math.pi),v1),
                      (start/(2*math.pi)+section_width*t0/(2*math.pi),v1)])
    # Fractured end grain; taper rays outwards, concentric structure is textured.
    for side in (-1,1):
        cap=[]
        for ir in range(Nr+1):
            rad=ir/Nr
            row=[]
            for ia in range(Na+1):
                t=ia/Na
                z=z_edge(t,side,rad)+(.004*math.sin(rad*80+phase))
                row.append(vertex(xyz(t,z,rad)))
            cap.append(row)
        for ir in range(Nr):
            for ia in range(Na):
                b=(cap[ir][ia],cap[ir+1][ia],cap[ir+1][ia+1],cap[ir][ia+1])
                if side<0: b=tuple(reversed(b))
                uv=[(.5+vertices[j][0]*.69,.5+vertices[j][1]*.72) for j in b]
                quad(b,uv,1)
        # Thin radial inner wall closes physical mesh and avoids invalid open shells.
    for t,reverse in ((0,False),(1,True)):
        sidegrid=[]
        for iz in range(Nv+1):
            v=iz/Nv;z=z_edge(t,-1)*(1-v)+z_edge(t,1)*v
            row=[vertex(xyz(t,z,ir/Nr)) for ir in range(Nr+1)]
            sidegrid.append(row)
        for iz in range(Nv):
            for ir in range(Nr):
                b=(sidegrid[iz][ir],sidegrid[iz][ir+1],
                   sidegrid[iz+1][ir+1],sidegrid[iz+1][ir])
                if reverse:b=tuple(reversed(b))
                quad(b,[(start/(2*math.pi)+section_width*t/(2*math.pi),iz/Nv),
                        (start/(2*math.pi)+section_width*t/(2*math.pi),(iz+1)/Nv),
                        (start/(2*math.pi)+section_width*t/(2*math.pi),(iz+1)/Nv),
                        (start/(2*math.pi)+section_width*t/(2*math.pi),iz/Nv)])
    mesh=bpy.data.meshes.new('CharcoalWedgeMesh_%02d'%index)
    mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new('AnatomicCarbonSector_%02d'%index,mesh)
    bpy.context.collection.objects.link(ob);ob.parent=root
    mesh.materials.append(side_mat);mesh.materials.append(end_mat)
    uv_layer=mesh.uv_layers.new(name='Charcoal_Anatomic_UV')
    for poly,uvs,mi in zip(mesh.polygons,UV,mats):
        poly.material_index=mi
        poly.use_smooth=(mi==0)
        for li,co in zip(poly.loop_indices,uvs):
            uv_layer.data[li].uv=co
    objects.append(ob)
    return ob

# Irregular, asymmetric radial cleavage; never perfectly equal spokes.
spans=[0,.17,.39,.51,.71,.85,1.0]
angle0=.13
for i in range(len(spans)-1):
    build_sector(i,angle0+2*math.pi*spans[i],angle0+2*math.pi*spans[i+1])

# Delaminated carbonized fibres: tapered and lifted strips follow the grain,
# with torn ends rather than random chips attached to the surface.
def splinter(i):
    a=.13+rng.uniform(0,2*math.pi)
    zmid=rng.uniform(-.63,.62)
    height=rng.uniform(.19,.59)
    width=rng.uniform(.010,.046)
    tilt=rng.uniform(-.14,.14)
    depth=.60+rng.uniform(-.035,.026)
    verts=[];faces=[]
    for k in range(7):
        f=k/6;z=zmid+(f-.5)*height
        theta=a+tilt*(f-.5)
        lift=.009+.012*(1-math.sin(f*math.pi))
        w=width*(.18+.82*math.sin(math.pi*f)**.55)
        for t in (-1,1):
            th=theta+t*w
            r=depth+lift+.009*math.sin(f*22+i)
            verts.append((r*math.cos(th)*1.02,r*math.sin(th)*.87,z))
    for k in range(6):
        faces.append((k*2,k*2+1,k*2+3,k*2+2))
    me=bpy.data.meshes.new('CinderFlakeMesh_%02d'%i)
    me.from_pydata(verts,[],faces);me.update();me.materials.append(side_mat)
    ob=bpy.data.objects.new('AxialCarbonFlake_%02d'%i,me)
    bpy.context.collection.objects.link(ob);ob.parent=root
    uv=me.uv_layers.new()
    for p in me.polygons:
        p.use_smooth=False
        for li in p.loop_indices:
            idx=me.loops[li].vertex_index
            v=verts[idx]
            uv.data[li].uv=((math.atan2(v[1]/.87,v[0]/1.02)%(2*math.pi))/(2*math.pi),.5+v[2]*.45)
    objects.append(ob)
for i in range(54): splinter(i)

# Render a physically plausible studio object, with no cartoon emissive or fake ash glow.
world=bpy.context.scene.world
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.24,.26,.29,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55
def area(name,pos,energy,size,temperature=None):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy
    data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    obj.location=pos;obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Large_softbox',(3,-4,5),1050,3.7)
area('Long_fibre_grazing_light',(-3,1.9,2.8),1300,2.6)
area('Low_fill',(-1,-3,-1.5),490,4.5)

cam_data=bpy.data.cameras.new('ReviewCamera');cam_data.type='ORTHO'
cam=bpy.data.objects.new('ReviewCamera',cam_data)
bpy.context.collection.objects.link(cam);bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.render.resolution_x=1100;scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
cam_data.ortho_scale=3.25
for label,pos,scale in [
    ('three_quarter',(3.8,-4.8,2.6),3.23),
    ('side',(6,-1,1.2),3.12),
    ('front_end',(1.5,-2.8,5.0),2.76),
    ('rear_end',(-2.8,2.8,-4.6),2.76),
    ('macro_fibres',(2.6,-4.0,1.4),1.79),
]:
    cam.location=pos
    cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    cam_data.ortho_scale=scale
    scene.render.filepath=str(OUT/(label+'.png'))
    bpy.ops.render.render(write_still=True)

# Saved source, real embedded PBR, full-resolution game-candidate GLB.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'PG_Charcoal_Hero_V003_MASTER.blend'))
bpy.ops.object.select_all(action='DESELECT')
for ob in objects: ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/'PG_Charcoal_Hero_V003_MASTER.glb'),export_format='GLB',use_selection=True)
polys=sum(len(ob.data.polygons) for ob in objects)
audit={
 'asset':'PG_Charcoal_Hero_V003','review':'candidate_not_approved',
 'construction':'6 coherent radial sectors + axial carbon flake geometry',
 'origin':'Original procedural anatomical sculpt; no stock photo textures copied',
 'references':['BlendKit Burnt Log 01 (CC0 photogrammetry)',
               'Barauna et al. 2021 BioResources carbonized wood anatomy',
               'Cary Institute wood charcoal close-up'],
 'source_license':'Original Project Genesis',
 'objects':len(objects),'mesh_polygons':polys,'pbr_texture_resolution':1536,
 'texture_sets':['axial basecolor/normal/roughness','endgrain basecolor/normal/roughness'],
 'views':['three_quarter','side','front_end','rear_end','macro_fibres'],
 'accepted_into_game':False
}
(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2))
print('PG_CHARCOAL_V003_RENDERED',json.dumps(audit))
