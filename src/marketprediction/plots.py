import numpy as np
import pandas as pd
import plotly.graph_objects as go


def plot_return(wallet, data, tickers):
    total_wallet = pd.Series(wallet['Total'])
    strategy_return = np.log(total_wallet / total_wallet.shift(1))
    market_return = {
        ticker: (np.log(
            data[f'Close {ticker}'] / data[f'Close {ticker}'].shift(1)
        ))
        for ticker in tickers
    }
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index[1:],
        y=strategy_return[1:],
        name="Strategy Return"
    ))
    for ticker in tickers:
        fig.add_trace(go.Scatter(
            x=data.index[1:],
            y=market_return[ticker][1:],
            name=f'Return {ticker}'
        ))
    fig.update_layout(title='Returns')
    fig.show()
