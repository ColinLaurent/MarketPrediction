import numpy as np
import pandas as pd


class Strategy:
    def generate_signals(
        self,
        data: pd.DataFrame,
        tickers: list[str]
    ) -> pd.DataFrame:
        """
        Return a f'Signal {ticker}' column
        1 -> buy ; 0 -> hold ; -1 -> sell
        """
        raise NotImplementedError("Strategy must implement generate_signals")


class TrendFollowingStrategy(Strategy):
    def __init__(self, ma_short=5, ma_long=20):
        self.ma_short = ma_short
        self.ma_long = ma_long

    def generate_signals(self, data, tickers):
        for ticker in tickers:
            ma_s = (data[f'Close {ticker}']
                    .shift(1).rolling(self.ma_short).mean())
            ma_l = (data[f'Close {ticker}']
                    .shift(1).rolling(self.ma_long).mean())
            data[f'Signal {ticker}'] = 0
            buy_mask = (ma_s > ma_l) & (ma_s <= ma_l).shift(1)
            sell_mask = (ma_s < ma_l) & (ma_s >= ma_l).shift(1)
            data.loc[buy_mask, f'Signal {ticker}'] = 1
            data.loc[sell_mask, f'Signal {ticker}'] = -1
        return data


class RSIStrategy(Strategy):
    def __init__(self, period=14, low=30, high=70):
        self.period = period
        self.high = high
        self.low = low

    def generate_signals(self, data, tickers):
        for ticker in tickers:
            close = data[f'Close {ticker}']
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(self.period).mean()
            avg_loss = loss.rolling(self.period).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi_raw = 100 - (100 / (1 + rs))
            rsi = rsi_raw.shift(1)

            data[f'RSI {ticker}'] = rsi
            data[f'Signal {ticker}'] = 0
            buy_mask = (rsi < self.low) & (rsi.shift(1) >= self.low)
            sell_mask = (rsi > self.high) & (rsi.shift(1) <= self.high)
            data.loc[buy_mask, f'Signal {ticker}'] = 1
            data.loc[sell_mask, f'Signal {ticker}'] = -1
        return data