import asyncio
from datetime import datetime
import re
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from api.auth import oauth2_scheme, get_current_user
from jose import jwt, JWTError
import httpx
from bs4 import BeautifulSoup
import feedparser
import requests
from sqlalchemy.orm import Session

from api.summarizer import summarize_articles, get_market_overview_summary
from database.models import get_db
from database.crud import create_trending_news, get_trending_news_by_link

router = APIRouter()

@router.get("/stock-data/")
async def get_stock_data(symbol: str = Query(...), current_user=Depends(get_current_user)):
    url = f"https://www.google.com/finance/quote/{symbol}:NSE"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=100.0, headers=headers) as client:
        resp = await client.get(url)
    data = parse_google_finance_data(resp.text)
    return JSONResponse(content={"symbol": symbol, **data})

def parse_google_finance_data(html):
    soup = BeautifulSoup(html, "html.parser")

    # Extract current price
    price_div = soup.find("div", class_="YMlKec fxKbKc")
    price = price_div.text.strip() if price_div else "N/A"

    # Extract other stock metadata
    stock_info = {
        "price": price,
        "revenue": "N/A",
        "profit": "N/A",
        "previous_close": "N/A",
        "day_range": "N/A",
        "year_range": "N/A",
        "market_cap": "N/A",
        "avg_volume": "N/A",
        "pe_ratio": "N/A",
        "dividend_yield": "N/A",
        "primary_exchange": "N/A",
    }

    # Try parsing the financial summary table
    summary_rows = soup.find_all("div", class_="gyFHrc")
    for row in summary_rows:
        try:
            label = row.find("div", class_="mfs7Fc").text.strip().lower()
            value = row.find("div", class_="P6K39c").text.strip()

            if "previous close" in label:
                stock_info["previous_close"] = value
            elif "day range" in label:
                stock_info["day_range"] = value
            elif "year range" in label:
                stock_info["year_range"] = value
            elif "market cap" in label:
                stock_info["market_cap"] = value
            elif "avg volume" in label or "volume" in label:
                stock_info["avg_volume"] = value
            elif "p/e ratio" in label:
                stock_info["pe_ratio"] = value
            elif "dividend yield" in label:
                stock_info["dividend_yield"] = value
            elif "primary exchange" in label:
                stock_info["primary_exchange"] = value
        except:
            continue

    # Also extract revenue and profit (like before)
    tables = soup.find_all('table', class_="slpEwd")
    for table in tables:
        for row in table.find_all('tr', class_="roXhBd"):
            cells = row.find_all('td')
            if len(cells) >= 2:
                label = cells[0].find('div', class_="rsPbEe").get_text(strip=True).lower()
                value = cells[1].get_text(strip=True)
                if 'revenue' in label and stock_info["revenue"] == "N/A":
                    stock_info["revenue"] = value
                if ('net profit margin' in label or 'profit' in label) and stock_info["profit"] == "N/A":
                    stock_info["profit"] = value

    return stock_info


def is_probable_article(div):
    text = div.get_text(separator='\n', strip=True)
    # Heuristics: at least 3 paragraphs, at least 500 chars, no "footer"/"copyright"/"related"/"advertisement"/"comments"
    if text.count('\n') < 3 or len(text) < 500:
        return False
    bad_keywords = ['copyright', 'footer', 'related', 'advertisement', 'comments']
    return not any(bad in text.lower() for bad in bad_keywords)

# --- Utility: Article Content Filter ---
def is_valid_article(item):
    article = item.get("article", "")
    return (
        article and
        not article.startswith("Error scraping") and
        not article.startswith("No article content found")
    )

# --- Google News Endpoint with Database Integration ---
@router.get("/google-news/")
async def get_google_news(
    symbol: str = Query(..., min_length=1, max_length=10),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        url = f"https://www.google.com/finance/quote/{symbol}:NSE"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            response = await client.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        news_items = soup.find_all("div", class_="yY3Lee")[:7]

        tasks = []
        links = []
        headlines = []
        for item in news_items:
            a_tag = item.find("a", href=True)
            headline_div = item.find("div", class_="Yfwt5")
            if a_tag and headline_div:
                link = a_tag['href']
                if link.startswith('/'):
                    link = f"https://www.google.com{link}"
                links.append(link)
                headlines.append(headline_div.get_text(strip=True))
                tasks.append(scrape_article_clean(link))

        articles = await asyncio.gather(*tasks)
        news_list = []
        for headline, link, article in zip(headlines, links, articles):
            news_list.append({
                "headline": headline,
                "link": link,
                "article": article
            })

        # Filter out empty/error articles
        filtered_news_list = list(filter(is_valid_article, news_list))

        # Summarize with trending news context from database
        summary = await summarize_articles(
            [item["article"] for item in filtered_news_list], 
            db=db, 
            symbol=symbol
        )

        return JSONResponse(content={
            "symbol": symbol.upper(),
            "news": filtered_news_list,
            "consolidated_summary": summary,
            "sources": [item["link"] for item in filtered_news_list]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News scraping failed: {str(e)}")

# --- Yahoo Trending News Endpoint with Database Storage ---
@router.get("/trending-news-india/")
async def get_trending_news_india(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    url = "https://news.search.yahoo.com/search?p=trending+indian+market+news"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        resp = await client.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    news_list = []
    tasks = []
    all_items = soup.select("li")  # Select all list items — many news results are in <li> elements

    # for li in soup.select("li.ov-a"):
    for li in all_items:
        li_class = li.get("class", [])
        if any("ad" in c for c in li_class):
            continue
        h4 = li.find("h4", class_="s-title")
        a = h4.find("a") if h4 else None
        headline = a.text.strip() if a else None
        link = a["href"] if a and a.has_attr("href") else None

        # Extract and clean the publisher link if it's a Yahoo redirect
        clear_link = None
        if link:
            unquoted_link = requests.utils.unquote(link)
            pattern = re.compile(r'RU=(.+?)/RK')
            match = re.search(pattern, unquoted_link)
            if match:
                clear_link = requests.utils.unquote(match.group(1))
            else:
                clear_link = link  # fallback to raw link if pattern not found

        snippet_tag = li.find("p", class_="s-desc")
        snippet = snippet_tag.text.strip() if snippet_tag else None

        if headline and clear_link:
            news_list.append({
                "headline": headline,
                "link": clear_link,
                "snippet": snippet,
                "article": None
            })
            tasks.append(scrape_article_clean(clear_link))

    articles_text = await asyncio.gather(*tasks)
    for i, article_text in enumerate(articles_text):
        news_list[i]["article"] = article_text

    # Filter out empty/error articles
    filtered_news_list = list(filter(is_valid_article, news_list))

    # Store trending news in database (avoid duplicates)
    stored_count = 0
    for item in filtered_news_list:
        try:
            # Check if news already exists
            existing_news = get_trending_news_by_link(db, item["link"])
            if not existing_news:
                create_trending_news(
                    db=db,
                    headline=item["headline"],
                    link=item["link"],
                    snippet=item["snippet"] or "",
                    article=item["article"] or ""
                )
                stored_count += 1
        except Exception as e:
            print(f"Error storing trending news: {str(e)}")
            continue
    print(stored_count)
    return JSONResponse(content={
        "news": filtered_news_list,
        "stored_in_db": stored_count,
        "total_fetched": len(filtered_news_list)
    })

# --- New Market Overview Endpoint ---
@router.get("/market-overview/")
async def get_market_overview(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive market overview based on trending news from database
    """
    try:
        summary = await get_market_overview_summary(db)
        return JSONResponse(content={
            "market_overview": summary,
            "generated_at": str(datetime.utcnow())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market overview generation failed: {str(e)}")

# --- Enhanced Stock Analysis Endpoint ---
@router.get("/stock-analysis/")
async def get_comprehensive_stock_analysis(
    symbol: str = Query(..., min_length=1, max_length=10),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive stock analysis including stock data, news, and market context
    """
    try:
        # Get stock data
        stock_url = f"https://www.google.com/finance/quote/{symbol}:NSE"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            stock_response = await client.get(stock_url)
        stock_data = parse_google_finance_data(stock_response.text)
        
        # Get stock news
        soup = BeautifulSoup(stock_response.text, "html.parser")
        news_items = soup.find_all("div", class_="yY3Lee")[:7]

        tasks = []
        stock_news = []
        for item in news_items:
            a_tag = item.find("a", href=True)
            headline_div = item.find("div", class_="Yfwt5")
            if a_tag and headline_div:
                link = a_tag['href']
                if link.startswith('/'):
                    link = f"https://www.google.com{link}"
                headline = headline_div.get_text(strip=True)
                stock_news.append({"headline": headline, "link": link})
                tasks.append(scrape_article_clean(link))

        articles = await asyncio.gather(*tasks)
        for i, article in enumerate(articles):
            stock_news[i]["article"] = article

        # Filter valid articles
        filtered_stock_news = list(filter(is_valid_article, stock_news))

        # Get comprehensive analysis with trending news context
        analysis = await summarize_articles(
            [item["article"] for item in filtered_stock_news], 
            db=db, 
            symbol=symbol
        )

        return JSONResponse(content={
            "symbol": symbol.upper(),
            "stock_data": stock_data,
            "stock_news": filtered_stock_news,
            "comprehensive_analysis": analysis,
            "analysis_timestamp": str(datetime.utcnow())
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stock analysis failed: {str(e)}")

# --- Example scrape_article_clean (unchanged) ---
async def scrape_article_clean(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            resp = await client.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(['aside', 'footer', 'nav', 'form', 'script', 'style', 'header', 'noscript']):
            tag.decompose()
        article = soup.find('article')
        if article:
            text = article.get_text(separator='\n', strip=True)
        else:
            candidates = []
            common_classes = [
                'article-content', 'story-body', 'main-content', 'content__article-body',
                'entry-content', 'post-content', 'news-content', 'article__content',
                'caas-body', 'caas-content', 'body__inner', 'story__content'
            ]
            for class_name in common_classes:
                div = soup.find('div', class_=class_name)
                if div:
                    candidates.append(div)
            if not candidates:
                divs = soup.find_all('div')
                probable_divs = [d for d in divs if is_probable_article(d)]
                if probable_divs:
                    main_content = max(probable_divs, key=lambda d: len(d.get_text(strip=True)))
                    text = main_content.get_text(separator='\n', strip=True)
                else:
                    text = ""
            else:
                main_content = max(candidates, key=lambda d: len(d.get_text(strip=True)))
                text = main_content.get_text(separator='\n', strip=True)
        lines = [line for line in text.split('\n') if len(line.strip()) > 20]
        return '\n'.join(lines[:50]) if lines else "No article content found."
    except Exception as e:
        return f"Error scraping article: {str(e)}"