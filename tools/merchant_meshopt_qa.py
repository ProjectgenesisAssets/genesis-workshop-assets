from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import json,sys
folder=Path(sys.argv[1])
source=Path(sys.argv[2])
variants=[p.stem for p in sorted((folder.parent/'inputs').glob('*.glb'))]
angles=[0,45,90,180,270]
def metrics(a,b):
    x=np.asarray(Image.open(a).convert("RGBA"),dtype=np.int16)
    y=np.asarray(Image.open(b).convert("RGBA"),dtype=np.int16)
    assert x.shape==y.shape
    A=x[:,:,3]>127; B=y[:,:,3]>127
    valid=A&B
    lumx=x[:,:,:3].mean(2);lumy=y[:,:,:3].mean(2)
    return {'silhouette_pct':round(100*np.count_nonzero(A^B)/max(1,np.count_nonzero(A)),4),
      'rgb_mae_pct':round(100*np.abs(x[:,:,:3]-y[:,:,:3])[valid].mean()/255,4),
      'new_dark_px':int(np.count_nonzero(valid&(lumx>80)&(lumy<45)&(lumx-lumy>55)))}
rows=[]
for tag in variants:
    samples={str(ang):metrics(folder/f'v01_{ang}.png',folder/f'{tag}_{ang}.png') for ang in angles}
    scores={'variant':tag,'source_bytes':source.stat().st_size,
         'candidate_bytes':(folder.parent/'inputs'/f'{tag}.glb').stat().st_size,
         'scores':samples}
    rows.append(scores)
    print('VARIANT',json.dumps(scores),flush=True)
(folder/'meshopt_qa.json').write_text(json.dumps(rows,indent=2))
for tag in variants:
    w,h=Image.open(folder/'v01_0.png').size
    board=Image.new('RGB',(w*len(angles),h*2+30),(35,42,54))
    d=ImageDraw.Draw(board)
    for i,angle in enumerate(angles):
        for row,name in enumerate(('v01',tag)):
            image=Image.open(folder/f'{name}_{angle}.png').convert('RGBA')
            background=Image.new('RGBA',image.size,(35,42,54,255))
            background.alpha_composite(image)
            board.paste(background.convert('RGB'),(i*w,row*(h+15)+15))
            d.text((i*w+8,row*(h+15)+1),f'{name} {angle} degrees',fill='white')
    board.save(folder/f'comparison_{tag}.jpg',quality=92)
