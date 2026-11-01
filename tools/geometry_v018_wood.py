"""V018 hand-split hardwood — reduce CNC/washboard fracture grooves, expose
both oak bark and torn core, keep ash's front-facing pale inner grain.
Only one connected mesh; preserve all V017 and V016 candidates.
"""
from math import sin,cos,pi,exp
_prior_wood_v017=wood_piece
def wood_piece(label,oak,offset):
    ob=_prior_wood_v017(label,oak,offset)
    segments=64;cols=56;arc=33
    if len(ob.data.vertices)!=segments*cols:
        raise RuntimeError("V018 requires the original single V017 split-log topology")
    radius=.257 if oak else .206
    for j in range(segments):
        t=j/(segments-1)
        drift=.016*sin(5*t+offset)+.007*sin(16*t+offset*.7)
        for k in range(arc,cols):
            h=(k-arc+1)/(cols-arc+1)
            vert=ob.data.vertices[j*cols+k]
            # Remove repeating wide sinusoidal hollows: these looked like
            # upholstery or corrugated rubber rather than dry wooden fibers.
            # Sparse, slowly wandering split ridges follow the longitudinal grain.
            ridge_center=.29+.065*sin(3.7*t+.4)
            thin_center=.74-.039*sin(4.4*t+.8)
            a=.010*exp(-((h-ridge_center)/.085)**2)
            b=-.007*exp(-((h-thin_center)/.071)**2)
            c=.003*sin(h*11.7+t*2.1)+.0018*sin(h*26.4-t*4.7)
            jag=.004*sin(t*13.3+h*9.8)*exp(-((h-.46)/.24)**2)
            physical=drift+a+b+c+jag
            vert.co.y=vert.co.y*.12+physical*.88
            # A few tiny asymmetric long-grain tears, not detached splinter meshes.
            vert.co.z+=.0018*sin(17.1*t+h*5.7)
    ob.data.update()
    # Oak should show approximately half bark + split interior (not a cylinder).
    # Rotation is around its longitudinal X axis, never an end-on billboard.
    ob.rotation_euler.x=1.22 if oak else .08
    ob["presentation"]="outer bark plus exposed radial split" if oak else "exposed pale ash fibers and thin bark strip"
    ob["surface_relief"]="faceted natural rifts, no regular fluting"
    return ob
