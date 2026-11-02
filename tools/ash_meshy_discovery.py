import asyncio,json,re
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
terms=["stacked logs","forest log","firewood stack","wood pile","wooden plank","weathered plank",
 "rustic plank patterns","log slice","stack of logs","wood log","stacked firewood",
 "pile of cut wooden logs","lumberyard","log bundle"]
async def main():
 out=Path("output");out.mkdir(exist_ok=True)
 records=[];unique={}
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
  page=await browser.new_page(viewport={"width":1200,"height":900})
  for url in pages:
   try:
    resp=await page.goto(url,wait_until="domcontentloaded",timeout=40000)
    await page.wait_for_timeout(1300)
    cards=await page.evaluate("""(terms)=>{
      let out=[];
      const titles=[...document.querySelectorAll('div,span,h3,p')].filter(el=>{
         const text=(el.textContent||'').trim().toLowerCase();
         return terms.some(v=>text===v||text.startsWith(v+','));
      });
      for(const el of titles){
        let card=el;
        for(let i=0;i<7&&card;i++,card=card.parentElement){
          const a=card.querySelector('a[href*="/posts/"]');
          if(a){
            const img=a.querySelector('img');
            out.push({title:(el.textContent||'').trim().slice(0,240),post:new URL(a.getAttribute('href'),location.origin).href,
              image:img?.currentSrc||img?.src||null, alt:img?.alt||null});
            break;
          }
        }
      }
      return [...new Map(out.map(row=>[row.post,row])).values()].slice(0,80);
    }""",terms)
    records.append({"url":url,"status":resp.status if resp else None,"cards":cards})
    for c in cards:unique.setdefault(c["post"],c)
    print("PAGE",url,"STATUS",resp.status if resp else None,"MATCHES",len(cards),flush=True)
    for c in cards[:18]:print("CANDIDATE",c["title"][:85],c["post"],flush=True)
   except Exception as e:
    print("ERROR",url,str(e)[:140],flush=True)
    records.append({"url":url,"error":str(e)[:250]})
   finally:
    (out/"meshy_geometry_discovery.json").write_text(json.dumps(records,ensure_ascii=False,indent=2))
  await browser.close()
 (out/"meshy_candidate_posts.json").write_text(json.dumps(list(unique.values()),ensure_ascii=False,indent=2))
 print("UNIQUE_CANDIDATES",len(unique),flush=True)
asyncio.run(main())