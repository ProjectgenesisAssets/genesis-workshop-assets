"""Genesis V017 — single hand-split hardwood billet and ONE realistic rolled hide.
Art-directed from the owner's split-firewood and partially unrolled leather references.
Preserve prior source scripts and source CC0 maps; this module replaces ONLY
wood_piece() and hide(). No overlapping duplicative pieces or piled leather sheets.
"""
import math,random
from math import sin,cos,pi,exp
from mathutils import Vector

def _matte_edge(original, name, tone):
    m=original.copy();m.name=name
    bs=m.node_tree.nodes.get("Principled BSDF")
    original_link=bs.inputs["Base Color"].links
    nodes=m.node_tree.nodes; links=m.node_tree.links
    if original_link:
        from_socket=original_link[0].from_socket
        tint=nodes.new("ShaderNodeMixRGB");tint.blend_type="MULTIPLY"
        tint.inputs[0].default_value=1.0
        tint.inputs[2].default_value=(*tone,1)
        links.new(from_socket,tint.inputs[1])
        links.new(tint.outputs["Color"],bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value=.87
    return m

def wood_piece(label,oak,offset):
    """A SINGLE longitudinally split half-log: convex bark and torn inner wood.
    Oak intentionally presents bark; ash presents pale split fibers toward camera.
    No overlapping leños and no detached interior chunks.
    """
    bark=v4_bark_material()
    end=v4_endgrain_material()
    radius=.257 if oak else .206
    length=1.49 if oak else 1.63
    n_arc=33;n_inner=23;n_section=64
    # Choose which face the inventory camera can see, by material.
    bark_direction=-1 if oak else 1
    v=[];uv=[];faces=[];indices=[]
    for j in range(n_section):
        t=j/(n_section-1)
        # wood is wider at butt, tapered and irregular with moisture shrinkage
        taper=1-.12*t+.017*sin(9.1*t+(.1 if oak else 1.2))
        rr=radius*taper
        drift_y=.016*sin(5*t+offset)+.007*sin(16*t+offset*.7)
        drift_z=.008*sin(7.1*t+.2*offset)
        for k in range(n_arc+n_inner):
            if k<n_arc:
                a=-pi/2+pi*k/(n_arc-1)
                yy=bark_direction*rr*cos(a)*(1+.043*sin(a*7+8*t))
                zz=rr*sin(a)
                yy+=.009*sin(a*13+t*17)+.003*sin(a*31+t*9)
            else:
                h=(k-n_arc+1)/(n_inner+1)
                yy=.019*sin(h*11+t*3.5+offset)
                yy+=.012*sin(h*23-t*7.5)
                yy+=.006*sin(h*37+t*18.1)
                # Longish raised splinter grooves; keep them shallow rather than a
                # uniformly CNC-carved washboard effect.
                yy+=.023*exp(-((h-(.29+.09*sin(t*4.2)))/.10)**2)
                zz=rr*(1-2*h)
            x=length*(t-.5)
            # A physically broken end creates chipped edges; only the end quarters vary.
            if t<.10:
                x+=(1-t/.10)**3*(.018*sin(k*4.7+offset)**2)
            if t>.90:
                x-=((t-.90)/.10)**3*(.029*sin(k*5.9+offset)**2)
            y=yy+drift_y
            z=rr+zz+drift_z+.032
            v.append((x,y,z))
            uv.append((t*(2.2 if oak else 2.8),k/(n_arc+n_inner-1)))
    n=n_arc+n_inner
    for j in range(n_section-1):
        for k in range(n):
            a=j*n+k;b=j*n+(k+1)%n
            faces.append((a,b,b+n,a+n))
            indices.append(1 if k<n_arc-1 else 0)
    faces.append(tuple(reversed(range(n))));indices.append(2)
    faces.append(tuple((n_section-1)*n+k for k in range(n)));indices.append(2)
    ob=mesh(label,v,faces,uv=uv,mats=[mat,bark,end],side_indices=indices)
    lay=ob.data.uv_layers.active
    # Endgrain rings are radially projected on wood ends, never projected sidegrain.
    for p in list(ob.data.polygons)[-2:]:
        for li in p.loop_indices:
            co=ob.data.vertices[ob.data.loops[li].vertex_index].co
            lay.data[li].uv=(.5+(co.y-drift_y)/(2.25*radius),.5+(co.z-radius-.032)/(2.25*radius))
    ob.rotation_euler=(0,0, -.085 if oak else .055)
    ob.location=(0,0,0)
    ob["actual_piece_count"]=1
    ob["presentation"]="bark forward" if oak else "exposed split wood forward"
    ob["true_solid_half_log"]=True
    return ob

def hide(cow):
    """One continuous cured leather strip rolled around a natural spiral,
    then partially unrolled to rest on the floor. Real thickness, open sides,
    no duplicated leather sheets. Inner and outer surfaces share true PBR.
    """
    width=1.18 if cow else .91
    inner=.130 if cow else .105
    outer=.188 if cow else .153
    thickness=.013 if cow else .0075
    centerz=outer+.047
    t_roll=.73
    n_path=192
    n_width=25
    turns=2.5 # final phase at 5pi: outer surface faces camera, then unrolls
    edge_mat=_matte_edge(mat,("bovine" if cow else "goat")+"_cut_edges",
                         (.70,.57,.47) if cow else (.77,.68,.60))
    verts=[];uv=[];faces=[];material_index=[]
    def smooth(u):
        u=max(0,min(1,u))
        return u*u*(3-2*u)
    def path(t):
        if t<=t_roll:
            q=t/t_roll
            theta=pi*2*turns*q
            r=inner+(outer-inner)*q
            yy=r*cos(theta)
            zz=centerz+r*sin(theta)
            return yy,zz,math.cos(theta),math.sin(theta)
        q=(t-t_roll)/(1-t_roll)
        # From outer roll at y=-outer,z=centerz, down to floor and smoothly
        # forward as a partially unrolled hide. No disconnected or duplicated sheet.
        drop=smooth(min(1,q/.46))
        travel=smooth(max(0,(q-.24)/.76))
        yy=-outer-.09*drop-(.62 if cow else .48)*travel
        zz=centerz-(centerz-.028)*drop
        zz+=.010*math.sin(q*2.7*pi)*q
        return yy,zz,0.0,1.0
    for layer in range(2):
        for j in range(n_path):
            t=j/(n_path-1)
            cy,cz,ny,nz=path(t)
            for i in range(n_width):
                u=i/(n_width-1)
                xx=width*(u-.5)
                # Hand-cut leather edge irregularity only toward the far sides.
                rim=(abs(2*u-1)**7)
                xx+=rim*(.015 if cow else .019)*sin(t*22+u*7.0)
                # A few shallow fold tensions on the visible unrolled flap.
                loose=max(0,(t-t_roll)/(1-t_roll))
                fold=(.018 if cow else .030)*sin(9*u+1.4*t)*loose**1.5
                fold+=.009*sin(20*u+2*t)*loose**2
                z=cz+fold
                y=cy+(.009 if cow else .012)*loose*loose*sin(4.3*u)
                if layer:
                    # On the tightly rolled part, displacement follows the radial
                    # surface normal, not vertical world Z.
                    y-=thickness*ny
                    z-=thickness*nz
                verts.append((xx,y,z))
                uv.append((u,t*3.2))
    layer_vertices=n_path*n_width
    for layer in range(2):
        base=layer*layer_vertices
        for j in range(n_path-1):
            for i in range(n_width-1):
                a=base+j*n_width+i
                b=a+1;c=b+n_width;d=a+n_width
                faces.append((a,b,c,d) if layer==0 else (d,c,b,a))
                material_index.append(0)
    for j in range(n_path-1):
        # actual thin cut edge along each side, not overlapping full skins
        for i in (0,n_width-1):
            a=j*n_width+i;b=(j+1)*n_width+i
            faces.append((a,b,layer_vertices+b,layer_vertices+a))
            material_index.append(1)
    for j in (0,n_path-1):
        for i in range(n_width-1):
            a=j*n_width+i;b=a+1
            faces.append((a,layer_vertices+a,layer_vertices+b,b))
            material_index.append(1)
    ob=mesh("single_partially_unrolled_"+("bovine" if cow else "goatskin")+"_leather",
            verts,faces,uv=uv,mats=[mat,edge_mat],side_indices=material_index)
    ob["single_continuous_hide"]=True
    ob["actual_piece_count"]=1
    ob["cut_thickness_m"]=thickness
    ob["roll_turns"]=turns
    ob["exposed_unrolled_tail"]=True
    return ob
