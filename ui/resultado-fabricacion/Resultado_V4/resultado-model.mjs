export const RAREZAS = Object.freeze(['Inútil','Común','Bueno','Excelente','Raro','Épico','Legendario','Mítico']);
const str=x=>typeof x==='string'?x.trim():'';
function fail(msg){throw new Error('Resultado inválido: '+msg);}
export function crearSnapshotResultado(r){
  if(!r || !str(r.id) || !str(r.nombre)) fail('id/nombre requeridos');
  if(!RAREZAS.includes(r.rareza)) fail('rareza desconocida');
  if(!str(r.asset?.glb)) fail('GLB original requerido');
  if(!Array.isArray(r.canales)) fail('canales requeridos');
  const ids=new Set();
  const canales=r.canales.map((c,i)=>{
    const id=str(c.id||c.key||c.nombre).toLowerCase();
    if(!id || ids.has(id)) fail('canal ausente o repetido');
    ids.add(id);
    const valor=Number(c.valor);
    if(!Number.isFinite(valor)||valor<0) fail('valor de canal inválido');
    return {id,nombre:str(c.nombre)||id,valor,ordenObtencion:Number.isInteger(c.ordenObtencion)?c.ordenObtencion:i,indice:i,
      tecnicas:(c.tecnicas||[]).map((t,j)=>{
        if(!str(t.nombre)) fail('técnica sin nombre');
        if(t.valor!=null&&!Number.isFinite(Number(t.valor))) fail('valor de técnica inválido');
        return {id:str(t.id)||id+'-'+j,nombre:str(t.nombre),valor:t.valor==null?null:Number(t.valor),
          descripcion:str(t.descripcion),visualFx:str(t.visualFx)||null};
      })};
  }).sort((a,b)=>a.ordenObtencion-b.ordenObtencion||a.indice-b.indice);
  const visualFx=(r.visualFx||[]).map((f,i)=>{
    const canalId=str(f.canalId).toLowerCase(),intensity=Number(f.intensity);
    if(!ids.has(canalId)||!Number.isFinite(intensity)||intensity<0||intensity>100)fail('VFX inválido');
    return {id:str(f.id)||'fx-'+i,canalId,intensity,animationClip:str(f.animationClip)||null,materialPreset:str(f.materialPreset)||null};
  });
  return {schemaVersion:1,id:r.id,recetaId:str(r.recetaId),nombre:r.nombre,rareza:r.rareza,asset:{
    glb:r.asset.glb,animationClips:(r.asset.animationClips||[]).filter(x=>str(x)),visualVariant:str(r.asset.visualVariant)||null},
    canales:canales.map(({indice,...c})=>c),visualFx,descripcionNGE:str(r.descripcionNGE),createdAt:str(r.createdAt)||null};
}
export function crearVistaResultado(r){
  const s=crearSnapshotResultado(r);
  return {titulo:s.nombre,insigniaRareza:s.rareza,descripcion:s.descripcionNGE,filas:s.canales.map(c=>({
    id:c.id,nombre:c.nombre,valor:c.valor,expandible:c.tecnicas.length>0,tecnicas:c.tecnicas})),
    visor:{glb:s.asset.glb,rotation:{enabled:true,yawRange:360},animationClips:s.asset.animationClips,
      visualFx:s.visualFx},registroId:s.id};
}
export function congelarResultado(r){const s=crearSnapshotResultado(r);const freeze=o=>{if(o&&typeof o==='object'){Object.values(o).forEach(freeze);Object.freeze(o)}return o};return freeze(s)}
