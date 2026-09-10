import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://ganjoor.net/moulavi/shams/ghazalsh/sh"
START = 1
END = 3230
CONCURRENCY = 50          # parallel requests
TIMEOUT = 15
OUTPUT_FILE = "ghazals_complete.md"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GhazalBot/1.0)"}


async def fetch(session, url, number, sem):
    async with sem:
        for attempt in range(3):
            try:
                async with session.get(url, timeout=TIMEOUT) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    html = await resp.text()
                    return parse(html, number)
            except Exception:
                await asyncio.sleep(0.5 * (attempt + 1))
        return None


def parse(html, number):
    soup = BeautifulSoup(html, "lxml")
    poem = soup.find("div", class_="poem") or soup.find("div", class_="b")
    if not poem:
        return None

    verses = []
    for v in poem.find_all("div", class_="b"):
        m1 = v.find("div", class_="m1")
        m2 = v.find("div", class_="m2")
        if m1 and m2:
            verses.append((m1.get_text(strip=True), m2.get_text(strip=True)))

    if not verses:
        return None
    return {"number": number, "verses": verses}


async def worker(session, number, sem, results):
    url = f"{BASE_URL}{number}"
    data = await fetch(session, url, number, sem)
    if data:
        results.append(data)
        print(f"[OK]   {number} ({len(data['verses'])} verses)")
    else:
        print(f"[FAIL] {number}")


async def main():
    sem = asyncio.Semaphore(CONCURRENCY)
    results = []

    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
        tasks = [worker(session, i, sem, results) for i in range(START, END + 1)]
        await asyncio.gather(*tasks)

    results.sort(key=lambda x: x["number"])
    write_markdown(results)
    print(f"\nDONE: {len(results)} ghazals saved to {OUTPUT_FILE}")


def write_markdown(data):
    lines = []
    lines.append("# دیوان شمس تبریزی - غزلیات\n")
    lines.append(f"**تعداد کل غزل‌ها:** {len(data)}\n")
    lines.append(f"**تاریخ تولید:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("---\n")

    for g in data:
        lines.append(f"## غزل {g['number']}\n")
        lines.append("```")
        for a, b in g["verses"]:
            lines.append(a)
            lines.append(b)
            lines.append("")
        lines.append("```\n")
        lines.append("---\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    asyncio.run(main())
