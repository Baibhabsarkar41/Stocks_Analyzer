import React, { useState, useEffect } from "react";
import { apiFetch } from "../api";
import { debounce } from "lodash"; // ensure lodash is installed

export default function StockScraperPage() {
  const [inputValue, setInputValue] = useState("");  // For input typing
  const [symbol, setSymbol] = useState("");          // Final selected symbol
  const [suggestions, setSuggestions] = useState([]);
  const [stockData, setStockData] = useState(null);
  const [trendnews, settrendnews] = useState(null);
  const [news, setNews] = useState([]);
  const [summary, setSummary] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(false);


  // Debounced suggestion fetcher
const fetchSuggestions = debounce(async (query) => {
  const cleaned = query.trim();
  if (cleaned === "") {
    setSuggestions([]);
    return;
  }

  try {
    const data = await apiFetch(`/api/search-symbol?query=${encodeURIComponent(cleaned)}`);
    setSuggestions(data);
  } catch (e) {
    setSuggestions([]);
  }
}, 300);


  // Fetch suggestions whenever inputValue changes
  useEffect(() => {
    if (!selected) {
      fetchSuggestions(symbol);
    }
  }, [symbol]);


const fetchStockData = async () => {
  if (!symbol) return;
  setLoading(true);
  setError("");
  try {
    const data = await apiFetch(`/api/stock-data/?symbol=${encodeURIComponent(symbol)}`);
    setStockData(data);

    const noData =
      (!data.price || data.price === "N/A") &&
      (!data.revenue || data.revenue === "N/A") &&
      (!data.profit || data.profit === "N/A");

    if (noData) {
      setError("No data available");
    }
  } catch (e) {
    setError("Failed to fetch stock data");
  }
  setLoading(false);
};


  const fetchNews = async () => {
    if (!symbol) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch(`/api/google-news/?symbol=${encodeURIComponent(symbol)}`);
      setNews(data.news || []);
      setSummary(data.consolidated_summary || "");
      setSources(data.sources || []);
    } catch (e) {
      setError("Failed to fetch news");
    }
    setLoading(false);
  };

  useEffect(() => {
    const lastFetch = localStorage.getItem("lastTrendFetch");
    console.log(lastFetch)
    if (!lastFetch) {
      fetchtrend();
    } else {
      const lastDate = new Date(lastFetch);
      const now = new Date();

      const oneDayMs = 24 * 60 * 60 * 1000;
      if (now - lastDate > oneDayMs) {
        fetchtrend();
      }
    }
  }, []);

  const fetchtrend = async () => {
    try {
      const data = await apiFetch(`/api/trending-news-india`);
      settrendnews(data.news);
      localStorage.setItem("lastTrendFetch", new Date().toISOString());
    } catch (e) {
      setError("Failed to fetch trending news");
    }
  };


  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <h2 style={{ marginBottom: "20px" }}>Stock Market Intelligence</h2>

<div style={{ display: "flex", alignItems: "flex-start", gap: "10px", marginBottom: "20px" }}>
  <div style={{ position: "relative", flex: "1" }}>
    <input
      value={symbol}
      onChange={e => {
        setSymbol(e.target.value);
        setSelected(false); // Re-enable suggestions if user edits input
      }}
      placeholder="Enter company name (e.g., Tata)"
      style={{
        padding: "8px",
        width: "100%",
        textTransform: "uppercase"
      }}
    />
    {suggestions.length > 0 && !selected && (
      <ul style={{
        listStyle: "none",
        margin: 0,
        padding: "5px",
        position: "absolute",
        top: "100%",
        left: 0,
        right: 0,
        backgroundColor: "#fff",
        border: "1px solid #ccc",
        maxHeight: "200px",
        overflowY: "auto",
        zIndex: 1000,
        boxShadow: "0px 4px 6px rgba(0,0,0,0.1)"
      }}>
        {suggestions.map((s, i) => (
          <li
            key={i}
            onClick={() => {
              setSymbol(s.symbol);
              setSelected(true);
              setSuggestions([]);
            }}
            style={{
              padding: "6px 10px",
              cursor: "pointer",
              borderBottom: "1px solid #eee"
            }}
          >
            <strong>{s.symbol}</strong> - {s.name}
          </li>
        ))}
      </ul>
    )}
  </div>

  <button 
    onClick={() => {
      fetchStockData();
      setSuggestions([]);  // Clear suggestions
      setSelected(true);   // Lock dropdown
    }}
    disabled={loading || !symbol}
    style={{ padding: "8px 16px" }}
  >
    Get Stock Data
  </button>

  <button 
    onClick={() => {
      fetchNews();
      setSuggestions([]);  // Clear suggestions
      setSelected(true);   // Lock dropdown
    }}
    disabled={loading || !symbol}
    style={{ padding: "8px 16px" }}
  >
    Analyze Market News
  </button>
</div>


      {/* <button
        onClick={fetchStockData}
        disabled={loading || !symbol}
        style={{ marginRight: "10px", padding: "8px 16px" }}
      >
        Get Stock Data
      </button>
      <button
        onClick={fetchNews}
        disabled={loading || !symbol}
        style={{ padding: "8px 16px" }}
      >
        Analyze Market News
      </button> */}

      {loading && <div style={{ color: "#666", margin: "10px 0" }}>Analyzing market data...</div>}
      {error && <div style={{ color: "red", margin: "10px 0" }}>{error}</div>}

      {stockData && (
        <div style={{
          margin: "20px 0",
          padding: "15px",
          border: "1px solid #e0e0e0",
          borderRadius: "8px"
        }}>
          <h3>Financial Overview</h3>
          <div><strong>Symbol:</strong> {stockData.symbol}</div>
          <div><strong>Current Price:</strong> {stockData.price}</div>
          <div><strong>Previous Close:</strong> {stockData.previous_close}</div>
          <div><strong>Day Range:</strong> {stockData.day_range}</div>
          <div><strong>52 Week Range:</strong> {stockData.year_range}</div>
          <div><strong>Market Cap:</strong> {stockData.market_cap}</div>
          <div><strong>Avg. Volume:</strong> {stockData.avg_volume}</div>
          <div><strong>P/E Ratio:</strong> {stockData.pe_ratio}</div>
          <div><strong>Dividend Yield:</strong> {stockData.dividend_yield}</div>
          <div><strong>Primary Exchange:</strong> {stockData.primary_exchange}</div>
          <div><strong>Revenue:</strong> {stockData.revenue}</div>
          <div><strong>Profit Margin:</strong> {stockData.profit}</div>
        </div>
      )}


      {/* Market Intelligence Summary */}
      {summary && (
        <div style={{
          margin: "20px 0",
          padding: "20px",
          backgroundColor: "#f8f9fa",
          borderRadius: "8px",
          boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
        }}>
          <h3 style={{ color: "#2c3e50", marginBottom: "15px" }}>Market Intelligence Report</h3>
          <div style={{
            whiteSpace: "pre-wrap",
            lineHeight: "1.6",
            borderLeft: "3px solid #3498db",
            paddingLeft: "15px"
          }}>
            {summary.split('\n').map((line, i) => (
              <p key={i} style={{ margin: "8px 0" }}>{line}</p>
            ))}
          </div>

          {sources.length > 0 && (
            <div style={{ marginTop: "20px" }}>
              <h4 style={{ color: "#2c3e50", marginBottom: "10px" }}>Sources Analyzed:</h4>
              <ul style={{ listStyle: "none", paddingLeft: "0" }}>
                {sources.map((url, i) => (
                  <li key={i} style={{ marginBottom: "5px" }}>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: "#2980b9",
                        textDecoration: "none",
                        display: "flex",
                        alignItems: "center"
                      }}
                    >
                      <span style={{ marginRight: "8px" }}>📰</span>
                      Source {i + 1} - {new URL(url).hostname}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Trending News */}
      {/* {trendnews && trendnews.map((n, i) => (
        <div
          key={i}
          style={{
            marginBottom: "20px",
            padding: "15px",
            border: "1px solid #e0e0e0",
            borderRadius: "8px"
          }}
        >
          <div style={{ marginBottom: "10px" }}>
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "10px"
            }}>
              <h4 style={{ margin: 0 }}>{n.headline}</h4>
              <a
                href={n.link}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: "#2980b9",
                  textDecoration: "none",
                  fontSize: "0.9em"
                }}
              >
                ↗ Full Article
              </a>
            </div>
            <div style={{
              fontSize: "0.9em",
              color: "#666",
              whiteSpace: "pre-wrap",
              maxHeight: "150px",
              overflow: "hidden",
              position: "relative"
            }}>
              {n.article}
              <div style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                height: "40px",
                background: "linear-gradient(transparent, white)"
              }} />
            </div>
          </div>
        </div>
      ))} */}

      {/* Detailed News */}
      {news.length > 0 && (
        <div style={{ marginTop: "30px" }}>
          <h3 style={{ color: "#2c3e50", marginBottom: "20px" }}>Detailed News Articles</h3>
          {news.map((n, i) => (
            <div
              key={i}
              style={{
                marginBottom: "20px",
                padding: "15px",
                border: "1px solid #e0e0e0",
                borderRadius: "8px"
              }}
            >
              <div style={{ marginBottom: "10px" }}>
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "10px"
                }}>
                  <h4 style={{ margin: 0 }}>{n.headline}</h4>
                  <a
                    href={n.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: "#2980b9",
                      textDecoration: "none",
                      fontSize: "0.9em"
                    }}
                  >
                    ↗ Full Article
                  </a>
                </div>
                <div style={{
                  fontSize: "0.9em",
                  color: "#666",
                  whiteSpace: "pre-wrap",
                  maxHeight: "150px",
                  overflow: "hidden",
                  position: "relative"
                }}>
                  {n.article}
                  <div style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: "40px",
                    background: "linear-gradient(transparent, white)"
                  }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
