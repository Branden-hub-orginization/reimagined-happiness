import asyncio, requests, random
from bs4 import BeautifulSoup
import aiohttp

SEARCH_TERMS = ["AI research","quantum gravity","cognitive science","emerging technology"]

async def scrape_loop():
    while True:
        term = random.choice(SEARCH_TERMS)
        url = f"https://duckduckgo.com/html/?q={term}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                html = await resp.text()
        soup = BeautifulSoup(html,"html.parser")
        links = [a.get("href") for a in soup.find_all("a",href=True)][:3]
        for link in links:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(link,timeout=10) as r:
                        text = await r.text()
                snippet = text[:1500]
                print("[AGENT] Learning from:", link)
                requests.post("http://localhost:8000/ask", params={"q": snippet})
            except: continue
        await asyncio.sleep(300)

if __name__=="__main__":
    asyncio.run(scrape_loop())
