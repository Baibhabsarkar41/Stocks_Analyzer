import os
import httpx
import re
from fastapi import HTTPException
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database.models import TrendingNews
from database.crud import get_latest_trending_news

load_dotenv()
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def format_summary(summary: str) -> str:
    # Bold section headers
    print(summary)
    summary = re.sub(r'\b(Starts:|Summary:|Key Points:)\b', r'**\1**', summary)
    # print(summary)
    # Bold numbered points like "1." or "2."
    summary = re.sub(r'(\n\s*\d+\.)', r'\n**\1**', summary)

    # Optionally: Underline instead of bold (if frontend supports HTML rendering)
    # summary = re.sub(r'\b(Starts:|Summary:|Key Points:)\b', r'<u>\1</u>', summary)

    return summary

async def summarize_articles(articles: list[str], db: Session = None, symbol: str = None) -> str:
    """
    Summarize articles with context from trending news in the database
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    if not articles:
        return "No articles to summarize."

    # Get trending news from database for context
    trending_context = ""
    if db:
        try:
            trending_news = get_latest_trending_news(db, limit=5)  # Get latest 5 trending news
            if trending_news:
                trending_headlines = [news.headline for news in trending_news if news.headline]
                trending_snippets = [news.snippet for news in trending_news if news.snippet]
                
                # Create trending news context
                trending_context = "\n\nCURRENT MARKET TRENDS (for additional context):\n"
                for i, news in enumerate(trending_news[:5], 1):
                    trending_context += f"{i}. {news.headline}"
                    if news.snippet:
                        trending_context += f" - {news.snippet[:100]}..."
                    trending_context += "\n"
        except Exception as e:
            print(f"Error fetching trending news: {str(e)}")
            trending_context = ""

    # Combine all articles, truncate if needed
    combined_text = "\n\n---\n\n".join([a[:2000] for a in articles])[:10000]  # Reduced to make room for trending news
    
    # Enhanced prompt with trending news context
    symbol_text = f" for {symbol.upper()}" if symbol else ""
    
    prompt = (
        f"You are a senior financial analyst with expertise in Indian stock markets. "
        f"Analyze the following news articles{symbol_text} and provide a comprehensive 5-point summary.\n\n"
        
        f"SPECIFIC STOCK NEWS{symbol_text}:\n{combined_text}\n"
        f"{trending_context}\n"
        
        f"Based on both the specific stock news and current market trends, provide analysis covering:\n"
        f"1. **Overall Market Sentiment**: Current mood and investor confidence\n"
        f"2. **Key Market Drivers**: Main factors influencing the stock/market\n"
        f"3. **Technical & Fundamental Outlook**: Price targets, financial health, growth prospects\n"
        f"4. **Risk Assessment**: Potential challenges and market risks\n"
        f"5. **Investment Recommendation**: Clear BUY/SELL/HOLD recommendation with rationale\n\n"
        
        f"Consider both the specific stock context and broader market trends in your analysis. "
        f"Be specific about price levels, timeframes, and confidence levels where applicable."
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GEMINI_API_URL,
                params={"key": GEMINI_API_KEY},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 1000,
                        "topP": 0.8,
                        "topK": 40
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return "Summary unavailable due to API error."

async def get_market_overview_summary(db: Session) -> str:
    """
    Generate a general market overview based on trending news only
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    try:
        # Get trending news from database
        trending_news = get_latest_trending_news(db, limit=10)
        if not trending_news:
            return "No trending news available for market overview."
        
        # Prepare trending news content
        trending_content = ""
        for i, news in enumerate(trending_news, 1):
            trending_content += f"{i}. **{news.headline}**\n"
            if news.snippet:
                trending_content += f"   {news.snippet}\n"
            if news.article and len(news.article) > 50:
                # Take first 300 chars of article if available
                trending_content += f"   {news.article[:300]}...\n"
            trending_content += "\n"
        
        prompt = (
            f"You are a senior financial market analyst. Based on the following trending Indian market news, "
            f"provide a comprehensive market overview with:\n\n"
            f"1. **Current Market Sentiment**: Overall mood and direction\n"
            f"2. **Key Market Themes**: Major trends and sectors in focus\n" 
            f"3. **Economic Indicators**: Important economic factors at play\n"
            f"4. **Sector Analysis**: Which sectors are performing well/poorly\n"
            f"5. **Market Outlook**: Short to medium-term market expectations\n\n"
            f"TRENDING MARKET NEWS:\n{trending_content}\n"
            f"Provide actionable insights for investors and traders."
        )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GEMINI_API_URL,
                params={"key": GEMINI_API_KEY},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 1200,
                        "topP": 0.8,
                        "topK": 40
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
    except Exception as e:
        print(f"Error generating market overview: {str(e)}")
        return "Market overview unavailable due to error."