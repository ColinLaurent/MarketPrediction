import numpy as np
import pandas as pd


def to_series_wallet_total(wallet: dict, index: pd.Index) -> pd.Series:
    """Transform wallet['Total'] into a Serie aligned on the price index."""
    ser = pd.Series(wallet['Total'], index=range(len(wallet['Total'])))
    if len(ser) >= 2 and len(index) >= (len(ser) - 1):
        ser.index = [-1] + list(index)[:len(ser) - 1]
        return ser.iloc[1:]
    return pd.Series(wallet['Total'][1:len(index) + 1], index=index)


def log_returns_from_total(wallet_total: pd.Series) -> pd.Series:
    return np.log(wallet_total / wallet_total.shift(1)).dropna()


def sharpe_ratio(returns: pd.Series, periods_per_year=252) -> float:
    if returns.std(ddof=0) == 0 or returns.dropna().empty:
        return np.nan
    return (returns.mean() / returns.std(ddof=0)) * np.sqrt(periods_per_year)


def max_drawdown(equity: pd.Series) -> float:
    roll_max = equity.cummax()
    dd = (equity / roll_max) - 1.0
    return float(dd.min()) if not dd.empty else np.nan


def basic_report(wallet: dict, price_index: pd.Index) -> dict:
    equity = to_series_wallet_total(wallet, price_index).astype(float)
    rets = log_returns_from_total(equity)
    return {
        "final_value": float(equity.iloc[-1]) if not equity.empty else np.nan,
        "return_total_pct": (
            float((equity.iloc[-1] / equity.iloc[0]) - 1)
            if len(equity) > 1 else np.nan),
        "sharpe": float(sharpe_ratio(rets, 252)),
        "max_drawdown": float(max_drawdown(equity)),
        "num_periods": int(len(equity))
    }
