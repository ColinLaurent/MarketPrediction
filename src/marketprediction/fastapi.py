from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
def home():
    return {"Message": "Hello FastAPI"}


@app.get("/backtest")
def backtest(ticker: str = "AAPL"):
    return {"ticker": ticker, "total_return": 0.12}


class BacktestRequest(BaseModel):
    ticker: str
    capital: float
    hold_max: int = 14


@app.post("/backtest")
def run_backtest(request: BacktestRequest):
    result = {
        "ticker": request.ticker,
        "capital": request.capital,
        "hold_max": request.hold_max,
        "performance": 0.12
    }
    return result
