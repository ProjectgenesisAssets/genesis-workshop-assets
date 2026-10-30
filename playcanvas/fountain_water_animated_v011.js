/* Project Genesis — Fountain V011 (PlayCanvas classic script).
 * Applies slow, coherent UV motion only to the fountain's AGUA_ materials.
 * Sculpted 8-second mesh animations come from the GLB and must also be played
 * by a PlayCanvas anim component. This script is not an MP4 substitute.
 * Mount on an instantiated GLB root, and supply the exported 2K normal map
 * if the GLB importer does not preserve it.
 */
var FountainWaterV011=pc.createScript('fountainWaterV011');
FountainWaterV011.attributes.add('normalTexture',{
  type:'asset',assetType:'texture',title:'V011 water normal map 2K'
});
FountainWaterV011.prototype.initialize=function(){
  this.elapsed=0;
  this.entries=[];
  this.replaced=[];
  var self=this;
  (this.entity.findComponents('render')||[]).forEach(function(render){
    (render.meshInstances||[]).forEach(function(mi){
      var original=mi.material;
      if(!original || !original.clone || !original.name ||
         original.name.indexOf('AGUA_')!==0)return;
      var pool=original.name.indexOf('Estanque')>=0;
      var jet=original.name.indexOf('Fisica')>=0;
      if(!pool&&!jet)return;
      var material=original.clone();
      material.name=original.name+'_V011_animated';
      if(self.normalTexture&&self.normalTexture.resource)
        material.normalMap=self.normalTexture.resource;
      if(!material.normalMap){
        console.warn('V011 fountain: missing normal map for',original.name);
        material.destroy();
        return;
      }
      material.normalMapTiling.set(pool?3.1:2.5,pool?3.1:2.5);
      material.normalDetailMap=material.normalMap;
      material.normalDetailMapTiling.set(pool?4.7:3.3,pool?4.7:3.3);
      material.update();
      self.replaced.push({mesh:mi,old:original});
      mi.material=material;
      self.entries.push({mat:material,pool:pool});
    });
  });
};
FountainWaterV011.prototype.update=function(dt){
  this.elapsed=(this.elapsed+Math.max(0,dt))%8;
  var t=this.elapsed;
  for(var i=0;i<this.entries.length;i++){
    var item=this.entries[i],m=item.mat;
    m.normalMapOffset.set(item.pool?t*.125:0,item.pool?-t*.125:t*.25);
    m.normalDetailMapOffset.set(item.pool?-t*.1875:t*.125,item.pool?t*.125:-t*.125);
    m.update();
  }
};
FountainWaterV011.prototype.destroy=function(){
  for(var i=0;i<this.replaced.length;i++)
    this.replaced[i].mesh.material=this.replaced[i].old;
  for(var j=0;j<this.entries.length;j++)
    this.entries[j].mat.destroy();
  this.replaced=[];
  this.entries=[];
};
