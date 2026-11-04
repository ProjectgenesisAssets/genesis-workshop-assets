'use strict';
/* PlayCanvas actual Chromium WebGL proof. No game repository modifications. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const out=path.resolve('reports/herrero-v082b-lossless-candidate');
fs.mkdirSync(out,{recursive:true});
async function main(){
 const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const results=[];
 try{
  for(const mode of [{name:'desktop',width:1200,height:720},{name:'mobile',width:844,height:390,mobile:true}]){
   const page=await browser.newPage({viewport:{width:mode.width,height:mode.height},isMobile:!!mode.mobile,hasTouch:!!mode.mobile,deviceScaleFactor:1});
   const errs=[];
   page.on('pageerror',e=>errs.push(String(e.message)));
   await page.goto('http://127.0.0.1:8278/browser-probe/',{waitUntil:'load',timeout:40000});
   const each=[];
   for(const file of ['/approved-original.glb','/lossless-candidate.glb']){
     await page.evaluate(filename=>{
       window.__doorStatus={ok:false,phase:'starting',error:null};
       window.__doorStatus.phase='loading';
       const asset=new pc.Asset('Door '+filename,'container',{url:filename,filename:filename.substring(1)});
       window.__pc_app.assets.add(asset);
       asset.once('load',()=>{
         try{
           const ent=asset.resource.instantiateRenderEntity();
           window.__pc_app.root.addChild(ent);
           const renderers=ent.findComponents('render');
           const instances=renderers.flatMap(c=>c.meshInstances||[]);
           const mats=[...new Set(instances.map(mi=>mi.material))];
           const maps=mats.flatMap(m=>['diffuseMap','normalMap','metalnessMap','glossMap','emissiveMap'].map(x=>m[x]).filter(Boolean));
           if(instances.length<5||mats.length<5||maps.length<10)throw Error('Missing PBR maps or primitive renderers '+JSON.stringify({instances:instances.length,mats:mats.length,maps:maps.length}));
           const info={loaded:true,renderers:renderers.length,instances:instances.length,materials:mats.length,pbrMaps:maps.length,
             textures:maps.map(x=>({width:x.width,height:x.height})).slice(0,20)};
           window.__doorStatus={ok:true,...info};
           ent.destroy();
         }catch(e){window.__doorStatus={ok:false,error:String(e.stack||e)}}
       });
       asset.once('error',e=>window.__doorStatus={ok:false,error:String(e?.stack||e)});
       window.__pc_app.assets.load(asset);
     },file);
     await page.waitForFunction(()=>window.__doorStatus&&(window.__doorStatus.ok===true||!!window.__doorStatus.error),null,{timeout:55000});
     const status=await page.evaluate(()=>window.__doorStatus);
     assert(status.ok,'PlayCanvas browser failed '+file+': '+JSON.stringify(status));
     each.push({file,...status});
   }
   assert.deepEqual(each[0].instances,each[1].instances,'Candidate lost mesh primitives');
   assert.deepEqual(each[0].materials,each[1].materials,'Candidate lost PBR materials');
   assert.deepEqual(each[0].pbrMaps,each[1].pbrMaps,'Candidate lost PBR texture maps');
   assert.equal(errs.length,0,'Browser page errors: '+errs.join('; '));
   const summary={mode:mode.name,original:each[0],candidate:each[1],browserErrors:errs,pass:true};
   console.log('PASS HERRERO LOSSLESS PLAYCANVAS '+mode.name.toUpperCase(),JSON.stringify(summary));
   results.push(summary);
   await page.close();
  }
 }finally{await browser.close()}
 fs.writeFileSync(out+'/playcanvas-browser.json',JSON.stringify({results},null,2));
}
main().catch(e=>{console.error('GLB WEBP IMPORT FAILED',e.stack||String(e));process.exitCode=1});
