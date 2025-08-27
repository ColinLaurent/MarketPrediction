import numpy as np
import plotly.graph_objects as go

def plot_return(wallet, data, tickers):
    strategy_return = [np.log(wallet['Total'][i+1] / wallet['Total'][i]) for i in range(len(wallet['Total']) - 1)]
    market_return = {}
    for ticker in tickers:
        market_return[ticker] = np.log(data[f'Close {ticker}'].shift(-1) / data[f'Close {ticker}'])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=strategy_return, name="Strategy Return"))
    for ticker in tickers:
        fig.add_trace(go.Scatter(x=data.index, y=market_return[ticker], name=f'Return {ticker}'))
    fig.update_layout(title='Returns')
    fig.show()