import pandas as pd
from fastapi import APIRouter, Query
from typing import List
from rapidfuzz import fuzz, process
import os

sym_router = APIRouter()

# Load CSV once during startup
# CSV_PATH = os.path.join(os.path.dirname(__file__), "../../symbolchange.csv")
CSV_PATH = os.path.join(os.path.dirname(__file__), "../../Symbols_NSE_India.csv")
df = pd.read_csv(CSV_PATH, header=None, usecols=[0, 1])  # 0 = symbol, 1 = name
df.columns = ["SYMBOL", "NAME"]  # Rename columns for convenience

# Clean up for matching
df["NAME"] = df["NAME"].astype(str).str.strip().str.upper()
df["SYMBOL"] = df["SYMBOL"].astype(str).str.strip().str.upper()

# Create a dictionary: name → symbol
company_dict = dict(zip(df["NAME"], df["SYMBOL"]))

@sym_router.get("/api/search-symbol")
def search_symbol(query: str = Query(..., min_length=1)) -> List[dict]:
    query = query.strip().upper()

    # Top 10 closest matches based on fuzz ratio
    matches = process.extract(query, company_dict.keys(), scorer=fuzz.partial_ratio, limit=10)

    # Filter results by threshold (optional: tweak to 70–90 depending on accuracy vs coverage)
    threshold = 70
    results = [{"name": name, "symbol": company_dict[name]} for name, score, _ in matches if score >= threshold]
    
    return results