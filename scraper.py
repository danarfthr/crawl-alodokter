import asyncio
import pandas as pd
import argparse
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

CATEGORIES = [
    "https://www.alodokter.com/kesehatan",
    "https://www.alodokter.com/keluarga",
    "https://www.alodokter.com/hidup-sehat"
]

BASE_URL = "https://www.alodokter.com"

async def get_article_links(crawler, category_url, pages=2):
    """Fetch article links from the category pages."""
    links = set()
    for page in range(1, pages + 1):
        url = category_url if page == 1 else f"{category_url}/page/{page}"
        print(f"Fetching category page {page}: {url}")
        
        result = await crawler.arun(url=url)
        if not result.success:
            print(f"Failed to fetch {url}: {result.error_message}")
            continue
            
        soup = BeautifulSoup(result.html, "lxml")
        
        # Alodokter uses <card-post-index url-path="..."> for article links
        cards = soup.find_all("card-post-index")
        for card in cards:
            path = card.get("url-path")
            if path:
                if not path.startswith("/"):
                    path = "/" + path
                links.add(BASE_URL + path)
                
    return list(links)

def extract_article_data(html, markdown, url):
    """Extract required fields from the article HTML and markdown."""
    soup = BeautifulSoup(html, "lxml")
    
    # Judul
    title_el = soup.find("h1")
    judul = title_el.text.strip() if title_el else ""
    
    # Isi and Konten
    isi = markdown
    
    # Referensi
    referensi = ""
    
    # Look for the specific data-sources div first
    ref_div = soup.find("div", class_="data-sources", style=False) # standard dom 
    if ref_div:
        referensi = ref_div.get_text(separator="\n").strip()
            
    # Peninjau
    peninjau = ""
    sources_div = soup.find("div", class_="sources", style=False) # standard dom
    if sources_div:
        for text in sources_div.stripped_strings:
            if "Ditinjau oleh" in text or "Ditulis oleh" in text:
                peninjau = text.strip()
                break
    
    if not peninjau:
        # Fallback to loose search, avoiding script/style tags
        for text_node in soup.find_all(string=lambda t: t and ("Ditinjau oleh" in t or "Ditulis oleh" in t)):
            if text_node.parent.name not in ["script", "style"]:
                text_content = text_node.strip()
                if "<div" in text_content and ">" in text_content: # It's a raw HTML string embedded in a JS var or similar
                    sub_soup = BeautifulSoup(text_content, "lxml")
                    # Set peninjau
                    for sub_text in sub_soup.stripped_strings:
                        if "Ditinjau oleh" in sub_text or "Ditulis oleh" in sub_text:
                            peninjau = sub_text.strip()
                            break
                    # Set referensi if not found
                    if not referensi:
                        sub_ref = sub_soup.find("div", class_="data-sources")
                        if sub_ref:
                            referensi = sub_ref.get_text(separator="\n").strip()
                else:
                    peninjau = text_content
                break

    # Tanggal Rilis
    tanggal = ""
    # Heuristic: look for 'Terakhir diperbarui'
    tanggal_el = soup.find(string=lambda t: t and "Terakhir diperbarui" in t)
    if tanggal_el:
        tanggal = tanggal_el.replace("Terakhir diperbarui:", "").strip()
    
    return {
        "Judul": judul,
        "Isi": isi,
        "Ringkasan": "", # To be filled by AI later
        "Referensi": referensi,
        "Tanggal Rilis": tanggal,
        "Peninjau": peninjau,
        "URL": url
    }

async def process_article(crawler, url):
    """Fetch and parse a single article."""
    print(f"Scraping article: {url}")
    result = await crawler.arun(url=url)
    if not result.success:
        print(f"Failed to scrape {url}")
        return None
        
    return extract_article_data(result.html, result.markdown, url)

async def main():
    async with AsyncWebCrawler() as crawler:
        all_links = set()
        for category in CATEGORIES:
            links = await get_article_links(crawler, category, pages=1) # limiting to 1 page for test/simple version
            all_links.update(links)
            
        all_urls = list(all_links)
        print(f"Found {len(all_urls)} unique articles to scrape.")
        
        parser = argparse.ArgumentParser(description="Scrape Alodokter articles.")
        parser.add_argument("--limit", type=int, help="Limit the number of articles to scrape")
        parser.add_argument("--test", action="store_true", help="Run a quick test scraping only 2 articles")
        # parse_known_args used so it doesn't fail if we run it via other tools/environments easily
        args, _ = parser.parse_known_args()
        
        if args.test:
            all_urls = all_urls[:2]
        elif args.limit and args.limit > 0:
            all_urls = all_urls[:args.limit]
        
        scraped_data = []
        for url in all_urls:
            data = await process_article(crawler, url)
            if data:
                scraped_data.append(data)
                
        # Save to CSV
        if scraped_data:
            df = pd.DataFrame(scraped_data)
            output_file = "alodokter_articles.csv"
            df.to_csv(output_file, index=False, encoding="utf-8")
            print(f"Successfully saved {len(scraped_data)} articles to {output_file}")
        else:
            print("No data was scraped.")

if __name__ == "__main__":
    asyncio.run(main())
