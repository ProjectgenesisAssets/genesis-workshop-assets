"""V018 Hemp: restrained extra flyaway fibers, rooted in the true three-strand coil.
Do not modify main form, original V017 scanned PBR or stable inventory display."""
import math
from mathutils import Vector
_old_hemp_v017=cord

def cord(hemp):
    result=_old_hemp_v017(hemp)
    if not hemp: return result
    coil=next((o for o in objects if o.name=="natural_hemp_three_strand_coil"),None)
    if coil is None or len(coil.data.vertices)!=3*460*7:
        raise RuntimeError("V018 hemp requires original 3-ply V017 strand mesh")
    # Ten new fine, SHORT strands: not giant hairs floating away from the coil.
    for i,j in enumerate((17,54,92,128,173,219,277,316,379,438)):
        strand=i%3
        k=(i*3+strand)%7
        idx=(strand*460+j)*7+k
        anchor=coil.data.vertices[idx].co.copy()
        prev=coil.data.vertices[idx-7].co.copy()
        tangent=(anchor-prev).normalized()
        lateral=Vector((-tangent.y,tangent.x,.16)).normalized()
        L=.008+.002*(i%4)
        end=anchor+tangent*L+lateral*(.42*L)
        near=anchor+lateral*.0007
        # Conical shard with direct mesh contact at source vertex.
        mesh("V018_attached_hemp_microfiber_%02d"%i,
             [tuple(anchor),tuple(near),tuple(end)],[(0,1,2)],mats=[mat])
    globals()["_v018_hemp_report"]={
      "additional_microfibers":10,
      "fibers_attached_to_existing_strand_vertices":True,
      "main_silhouette_preserved":True,
      "original_cc0_pbr_preserved":True,
    }
    return result
