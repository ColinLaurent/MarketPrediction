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
        for ticker in tickers:
            self.wallet[ticker] = [[0, 0]]

    def run(self):
        data = self.strategy.generate_signals(self.data, self.tickers)

        # Add possibility of selling to increase cash then buy the same day
        # Add hold_max

        for _, row in data.iterrows():
            current_total = 0
            current_cash = self.wallet['Cash'][-1]
            for ticker in self.tickers:
                current_pos = self.wallet[ticker][-1]
                if (
                    (row[f'Signal {ticker}'] == 1) and
                    (current_cash >= row[f'Open {ticker}'])
                ):
                    current_cash -= row[f'Open {ticker}']
                    self.wallet[ticker].append(
                        [current_pos[0] + 1,
                         current_pos[1] + row[f'Open {ticker}']]
                    )
                elif (row[f'Signal {ticker}'] == -1) and (current_pos[0] > 0):
                    current_cash += row[f'Open {ticker}']
                    self.wallet[ticker].append(
                        [current_pos[0] - 1,
                         current_pos[1] - row[f'Open {ticker}']]
                    )
                else:
                    self.wallet[ticker].append(current_pos)

                self.wallet[ticker][-1][1] = (self.wallet[ticker][-1][0] *
                                              row[f'Close {ticker}'])
                current_total += self.wallet[ticker][-1][1]

            self.wallet['Cash'].append(current_cash)
            self.wallet['Total'].append(current_total + current_cash)

        return
