/* Project Genesis — Dolphin Fountain V009 moving water normals.
 * REVIEW CANDIDATE. Do not install into production until approved.
 * Attach to imported fountain root; assign the exported water normal texture.
 * Only AGUA_ materials are touched; stone remains untouched.
 */
var FountainWaterV009=pc.createScript('fountainWaterV009');
FountainWaterV009.attributes.add('normalTexture',{
    type:'asset',assetType:'texture',title:'Water Ripples Normal 2K'
});
FountainWaterV009.prototype.initialize=function(){
    this.elapsed=0;
    this.waterMaterials=[];
    var that=this;
    (this.entity.findComponents('render')||[]).forEach(function(render){
        (render.meshInstances||[]).forEach(function(instance){
            var src=instance.material;
            if(!src || !src.name || !src.clone ||
               src.name.indexOf('AGUA_')!==0) return;
            var pool=src.name.indexOf('Estanque')>=0;
            var jet=src.name.indexOf('Fisica')>=0;
            if(!pool && !jet) return;
            var mat=src.clone();
            if(that.normalTexture && that.normalTexture.resource)
                mat.normalMap=that.normalTexture.resource;
            if(!mat.normalMap)return;
            mat.normalMapTiling.set(pool?4:2.5,pool?4:2.5);
            mat.normalDetailMap=mat.normalMap;
            mat.normalDetailMapTiling.set(pool?6.5:3.3,pool?6.5:3.3);
            mat.update();
            instance.material=mat;
            that.waterMaterials.push({mat:mat,pool:pool});
        });
    });
};
FountainWaterV009.prototype.update=function(dt){
    this.elapsed=(this.elapsed+dt)%8;
    var t=this.elapsed;
    this.waterMaterials.forEach(function(item){
        var mat=item.mat;
        mat.normalMapOffset.set(item.pool?t*.125:0,item.pool?-t*.125:t*.25);
        mat.normalDetailMapOffset.set(item.pool?-t*.1875:t*.125,item.pool?t*.125:-t*.125);
        mat.update();
    });
};
