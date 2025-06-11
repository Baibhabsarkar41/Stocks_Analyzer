from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from api.auth import oauth2_scheme, get_current_user  # Import get_current_user instead of get_user

class StockReport(BaseModel):
    stock_symbol: str
    gist: str
    sources: List[str]

api_router = APIRouter()

# Remove the duplicate get_current_user function since it's now in auth.py

# Dummy data collection and AI summarization
async def collect_stock_data(stock_symbol: str):
    return {
        "stock_symbol": stock_symbol,
        "reports": [
            "Report 1: Stock is performing well.",
            "Report 2: Analysts predict growth."
        ],
        "sources": [
            "https://example.com/report1",
            "https://example.com/report2"
        ]
    }

async def ai_summarize(reports: list[str]) -> str:
    return "Summary: Stock shows positive trends based on reports."

@api_router.get("/stocks/{stock_symbol}/raw")
async def get_raw_reports(stock_symbol: str, current_user=Depends(get_current_user)):
    data = await collect_stock_data(stock_symbol)
    return {"stock_symbol": stock_symbol, "reports": data["reports"], "sources": data["sources"]}

@api_router.get("/stocks/{stock_symbol}/gist", response_model=StockReport)
async def get_stock_gist(stock_symbol: str, current_user=Depends(get_current_user)):
    data = await collect_stock_data(stock_symbol)
    gist = await ai_summarize(data["reports"])
    return StockReport(stock_symbol=stock_symbol, gist=gist, sources=data["sources"])
