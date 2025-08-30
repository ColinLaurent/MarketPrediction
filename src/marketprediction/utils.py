import numpy as np
import pandas as pd

import plotly.graph_objects as go


class Strategy:
    def generate_signals(self, data, tickers):
        """Return a column 'signal' : 1 -> buy ; 0 -> hold ; -1 -> sell"""
        raise NotImplementedError("Strategy must implement generate_signals")


class TrendFollowingStrategy(Strategy):
    def __init__(self, ma_short=5, ma_long=20):
        self.ma_short = ma_short
        self.ma_long = ma_long

    def generate_signals(self, data, tickers):
        for ticker in tickers:
            data[f'MA_short {ticker}'] = (
                data[f'Close {ticker}']
                .shift(1)
                .rolling(window=self.ma_short)
                .mean()
            )
            data[f'MA_long {ticker}'] = (
                data[f'Close {ticker}']
                .shift(1)
                .rolling(window=self.ma_long)
                .mean()
            )
            data[f'Signal {ticker}'] = 0
            buy_mask = (
                (data[f'MA_short {ticker}'] > data[f'MA_long {ticker}'])
                &
                (data[f'MA_short {ticker}'] <= data[f'MA_long {ticker}'])
                .shift(1)
            )
            sell_mask = (
                (data[f'MA_short {ticker}'] < data[f'MA_long {ticker}'])
                &
                (data[f'MA_short {ticker}'] >= data[f'MA_long {ticker}'])
                .shift(1)
            )
            data.loc[buy_mask, f'Signal {ticker}'] = 1
            data.loc[sell_mask, f'Signal {ticker}'] = -1
        return data


class MovingAverageStrategy(Strategy):
    def __init__(self, ma_short=5, ma_long=30, thresh=0.9):
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.thresh = thresh

    def generate_signals(self, data, tickers):
        for ticker in tickers:
            data[f'MA_short {ticker}'] = (
                data[f'Close {ticker}']
                .shift(1)
                .rolling(window=self.ma_short)
                .mean()
            )
            data[f'MA_long {ticker}'] = (
                data[f'Close {ticker}']
                .shift(1)
                .rolling(window=self.ma_long)
                .mean()
            )
            data[f'Signal {ticker}'] = 0
            buy_mask = (
                (data[f'MA_short {ticker}'] <
                 self.thresh * data[f'MA_long {ticker}'])
                &
                (data[f'MA_short {ticker}'] >=
                 self.thresh * data[f'MA_long {ticker}'])
                .shift(1)
            )
            sell_mask = (
                (data[f'MA_short {ticker}'] >
                 (2 - self.thresh) * data[f'MA_long {ticker}'])
                &
                (data[f'MA_short {ticker}']
                 <= (2 - self.thresh) * data[f'MA_long {ticker}'])
                .shift(1)
            )
            data.loc[buy_mask, f'Signal {ticker}'] = 1
            data.loc[sell_mask, f'Signal {ticker}'] = -1
        return data


class Backtester:
    def __init__(
        self,
        tickers,
        data,
        strategy,
        hold_max=14,
        initial_capital=1000
    ):
        """
        Args:
            hold_max [int] : maximal number of days before selling a position
        """
        self.tickers = tickers
        self.data = data
        self.strategy = strategy
        self.hold_max = hold_max
        self.initial_capital = initial_capital
        self.wallet = {'Cash': [initial_capital], 'Total': [initial_capital]}
        self.positions = pd.DataFrame()
        for ticker in tickers:
            self.wallet[ticker] = [[0, 0]]

    def buy(self, ticker, price, date, quantity=1):
        if self.wallet['Cash'][-1] < price * quantity:
            return
        self.wallet['Cash'][-1] -= price * quantity
        self.wallet[ticker][-1][0] += quantity
        new_pos = {
            'Ticker': ticker,
            'Buy Date': date,
            'Buy Price': price,
            'Holding Days': 0,
            'Quantity': quantity
        }
        self.positions = pd.concat(
            [self.positions, pd.DataFrame([new_pos])],
            axis=0,
            ignore_index=True
        )
        return

    def sell(self, ticker, price, quantity=1):
        if self.wallet[ticker][-1][0] < quantity:
            return
        self.wallet['Cash'][-1] += price * quantity
        self.wallet[ticker][-1][0] -= quantity
        idx = (
            self.positions[self.positions['Ticker'] == ticker]
            ['Holding Days']
            .idxmax()
        )
        self.positions.loc[idx, 'Quantity'] -= 1
        if self.positions.loc[idx, 'Quantity'] == 0:
            self.positions = self.positions.drop(idx)
        return

    def sell_forced(self, ticker, price):
        old_pos = (
            (self.positions['Ticker'] == ticker) &
            (self.positions['Holding Days'] == self.hold_max)
        )
        if not self.positions.loc[old_pos].empty:
            quantity = self.positions.loc[old_pos, 'Quantity'].sum()
            self.wallet['Cash'][-1] += price * quantity
            self.wallet[ticker][-1][0] -= quantity
            self.positions = self.positions.drop(
                self.positions.loc[old_pos].index
            )
        return

    def run(self):
        data = self.strategy.generate_signals(self.data, self.tickers)

        for date, row in data.iterrows():
            self.wallet['Cash'].append(self.wallet['Cash'][-1])
            current_total_assets = 0
            for ticker in self.tickers:
                self.wallet[ticker].append([self.wallet[ticker][-1][0], 0])
                if not self.positions.empty:
                    self.sell_forced(ticker, row[f'Open {ticker}'])
                if row[f'Signal {ticker}'] == -1:
                    self.sell(ticker, row[f'Open {ticker}'])
                elif row[f'Signal {ticker}'] == 1:
                    self.buy(ticker, row[f'Open {ticker}'], date)
                self.wallet[ticker][-1][1] = (
                    self.wallet[ticker][-1][0] *
                    row[f'Close {ticker}']
                )
                current_total_assets += self.wallet[ticker][-1][1]
            self.wallet['Total'].append(
                current_total_assets +
                self.wallet['Cash'][-1]
            )
            if not self.positions.empty:
                self.positions['Holding Days'] += 1
        return

    def plot_wallet(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=self.data.index,
            y=self.wallet['Total'],
            name='Wallet'
        ))
        for ticker in self.tickers:
            fig.add_trace(go.Scatter(
                x=self.data.index,
                y=(self.data[f'Close {ticker}'] * self.initial_capital /
                   self.data[f'Close {ticker}'][0]),
                name=f'Normalized Close {ticker}'
            ))
        fig.update_layout(title="Wallet")
        fig.show()
        return

    def plot_return(self):
        total_wallet = pd.Series(self.wallet['Total'])
        strategy_return = np.log(total_wallet / total_wallet.shift(1))
        market_return = {
            ticker: (np.log(
                self.data[f'Close {ticker}'] /
                self.data[f'Close {ticker}'].shift(1)
            ))
            for ticker in self.tickers
        }
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=self.data.index[1:],
            y=strategy_return[1:],
            name="Strategy Return"
        ))
        for ticker in self.tickers:
            fig.add_trace(go.Scatter(
                x=self.data.index[1:],
                y=market_return[ticker][1:],
                name=f'Return {ticker}'
            ))
        fig.update_layout(title='Returns')
        fig.show()
