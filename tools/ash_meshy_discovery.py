import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright
pages=[
"https://www.meshy.ai/tags/firewood",
"https://www.meshy.ai/tags/lumber",
"https://www.meshy.ai/tags/plank",
"https://www.meshy.ai/tags/planks",
"https://www.meshy.ai/tags/timber",
"https://www.meshy.ai/tags/log",
]
terms=["Stacked Logs","Forest Log","Firewood Stack","Wood Pile","Wooden Plank",
 "wooden plank","Weathered Plank","Rustic Plank Patterns","Log Slice",
 "Stack of Logs","Tree Log","Wood Log"]
async def main():
 output=Path("output")
 output.mkdir(exist_ok=True)
 results=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=["--no-sandbox","--use-gl=angle","--use-angle=swiftshader"])
  page=await browser.new_page(viewport={"width":1365,"height":800})
  for url in pages:
   print("PAGE",url,flush=True)
   try:
    resp=await page.goto(url,wait_until="domcontentloaded",timeout=45000)
    await page.wait_for_timeout(6000)
    records=await page.evaluate("""(terms) => {
      const set=new Set(terms.map(v=>v.toLowerCase()));
      let out=[];
      const els=[...document.querySelectorAll('h3, h2, a, div, span, p')];
      for(const e of els){
        let t=(e.innerText||'').trim().replace(/\\s+/g,' ');
        if(!set.has(t.toLowerCase()))continue;
        let parents=[];
        let n=e;
        for(let i=0;n&&i<7;i++,n=n.parentElement){
          parents.push({tag:n.tagName,cls:String(n.className||'').slice(0,150),href:n.getAttribute('href'),
            role:n.getAttribute('role'),onclick:n.getAttribute('onclick'),html:n.outerHTML.slice(0,900)});
        }
        out.push({title:t,parents});
        if(out.length>=65)break;
      }
      let links=[...document.querySelectorAll('a[href]')].filter(a=>/posts\\/|3d-models\\//.test(a.href)).slice(0,100).map(a=>({text:(a.innerText||'').trim().slice(0,110),href:a.href}));
      let imgs=[...document.querySelectorAll('img')].slice(0,35).map(i=>({alt:i.alt,src:i.currentSrc||i.src}));
      return {records:out,links,imgs,title:document.title,bodyLength:document.body.innerText.length};
    }""",terms)
    html=await page.content()
    uuids=re.findall(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",html)
    records["url"]=url
    records["status"]=resp.status if resp else None
    records["uuid_count"]=len(uuids)
    results.append(records)
    print("PAGE_RESULT",json.dumps({k:v for k,v in records.items() if k not in ("records","imgs","links")}),"POST_LINKS",json.dumps(records["links"][:15]),flush=True)
    for item in records["records"][:25]:
     print("MATCH",item["title"],"HTML",json.dumps(item["parents"][:4])[:2600],flush=True)
   except Exception as e:
    results.append({"url":url,"error":str(e)})
    print("ERROR",url,str(e),flush=True)
  await browser.close()
 (output/"meshy_geometry_discovery.json").write_text(json.dumps(results,ensure_ascii=False,indent=2))
asyncio.run(main())