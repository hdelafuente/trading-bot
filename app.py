import dash
from dash import dcc, html, dash_table
import pandas as pd
from dash.dependencies import Input, Output
from bot import TradingBot
from utils import (
    API_KEY,
    API_SECRET,
    SYMBOLS,
    TIMEFRAME,
    LEVERAGE,
    RISK_BALANCE,
    STRATEGIES,
    load_backtest_results,
)
from plotly.subplots import make_subplots
import plotly.graph_objects as go

bot = TradingBot(
    api_key=API_KEY,
    api_secret=API_SECRET,
    leverage=LEVERAGE,
    risk_balance=RISK_BALANCE,
    max_positions=1,
)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div(
    [
        html.H1("Backtest Results"),
        dcc.Dropdown(
            id="strategy-dropdown",
            options=[{"label": strategy, "value": strategy} for strategy in STRATEGIES],
            value=STRATEGIES[0],  # Default strategy
            style={"margin-bottom": "20px"},
        ),
        dcc.Dropdown(
            id="symbol-dropdown",
            options=[{"label": symbol, "value": symbol} for symbol in SYMBOLS],
            value=SYMBOLS[0],  # Default value
            style={"margin-bottom": "20px"},
        ),
        dcc.Loading(
            id="loading-metrics",
            type="circle",
            children=[
                html.Div(
                    [
                        html.Div(
                            id="metrics-table",
                            style={
                                "margin-bottom": "20px",
                                "width": "50%",
                                "display": "inline-block",
                            },
                        ),
                        html.Div(
                            dcc.Graph(
                                id="pnl-bar-chart",
                                style={"margin-bottom": "20px"},
                            ),
                            style={"width": "50%", "display": "inline-block"},
                        ),
                    ],
                    style={"display": "flex"},
                ),
                dcc.Graph(
                    id="price-line-chart",
                    style={"margin-bottom": "20px"},
                ),
                dcc.Graph(
                    id="balance-line-chart",
                    style={"margin-bottom": "20px"},
                ),
                html.Div(
                    id="trades-table",
                    style={"margin-bottom": "20px"},
                ),
            ],
        ),
    ]
)


# Callback to update tables and charts based on selected symbol
@app.callback(
    [
        Output("metrics-table", "children"),
        Output("trades-table", "children"),
        Output("pnl-bar-chart", "figure"),
        Output("price-line-chart", "figure"),
        Output("balance-line-chart", "figure"),
    ],
    [Input("symbol-dropdown", "value"), Input("strategy-dropdown", "value")],
)
def update_content(selected_symbol: str, selected_strategy: str):
    # Instantiate TradingBot and fetch klines with indicators
    backtest_results = load_backtest_results(selected_strategy, selected_symbol)
    kl = bot.fetch_klines_with_indicators(selected_symbol, TIMEFRAME)

    signal = bot.strategy.get_signal(kl, selected_strategy)

    # Filter results for the selected symbol
    metrics_df = pd.DataFrame([backtest_results["metrics"]])
    trades_df = pd.DataFrame(backtest_results["trades"])
    del trades_df["open"]

    # Transpose the DataFrame to make it vertical
    metrics_df_vertical = metrics_df.T.reset_index()
    metrics_df_vertical.columns = ["Metric", "Value"]

    metrics_table = dash_table.DataTable(
        data=metrics_df_vertical.to_dict("records"),
        columns=[{"name": i, "id": i} for i in metrics_df_vertical.columns],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left"},
    )

    trades_table = dash_table.DataTable(
        data=trades_df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in trades_df.columns],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left"},
    )

    # Create a bar chart for PnL
    pnl_fig = {
        "data": [
            {
                "x": trades_df["exit_date"],
                "y": trades_df["pnl"],
                "type": "bar",
                "name": "PnL",
                "marker": {
                    "color": trades_df["pnl"].apply(
                        lambda x: "red" if x < 0 else "green"
                    )
                },
            },
        ],
        "layout": {
            "title": "PnL by Exit Date",
            "xaxis": {"title": "Exit Date"},
            "yaxis": {"title": "PnL"},
        },
    }

    # Separate winning and losing trades
    winning_trades = trades_df[trades_df["pnl"] > 0]
    losing_trades = trades_df[trades_df["pnl"] <= 0]

    # Create a subplot figure with 2 rows, setting the row heights
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Close Price with EMA 200", "RSI"),
        row_heights=[0.7, 0.3],  # 70% for the first row, 30% for the second row
    )

    # Add Close Price and EMA 200 to the first row
    fig.add_trace(
        go.Scatter(
            x=kl.index,
            y=kl["Close"],
            mode="lines",
            name="Close Price",
            hovertemplate="Date: %{x}<br>Close Price: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=kl.index,
            y=kl["ema_200"],
            mode="lines",
            name="EMA 200",
            line=dict(dash="dash", color="blue"),
            hovertemplate="Date: %{x}<br>EMA 200: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Add trade markers to the first row
    fig.add_trace(
        go.Scatter(
            x=winning_trades["entry_date"],
            y=winning_trades["entry_price"],
            mode="markers",
            name="Winning Trade Open",
            marker=dict(color="green", size=10),
            hovertemplate="Entry Date: %{x}<br>Entry Price: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=winning_trades["exit_date"],
            y=winning_trades["exit_price"],
            mode="markers",
            name="Winning Trade Close",
            marker=dict(color="green", size=10, symbol="x"),
            hovertemplate="Exit Date: %{x}<br>Exit Price: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=losing_trades["entry_date"],
            y=losing_trades["entry_price"],
            mode="markers",
            name="Losing Trade Open",
            marker=dict(color="red", size=10),
            hovertemplate="Entry Date: %{x}<br>Entry Price: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=losing_trades["exit_date"],
            y=losing_trades["exit_price"],
            mode="markers",
            name="Losing Trade Close",
            marker=dict(color="red", size=10, symbol="x"),
            hovertemplate="Exit Date: %{x}<br>Exit Price: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Add RSI to the second row
    fig.add_trace(
        go.Scatter(
            x=kl.index,
            y=kl["rsi"],
            mode="lines",
            name="RSI",
            line=dict(color="purple"),
            hovertemplate="Date: %{x}<br>RSI: %{y}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    # Add horizontal lines for RSI levels
    fig.add_shape(
        type="line",
        x0=kl.index.min(),
        x1=kl.index.max(),
        y0=70,
        y1=70,
        line=dict(dash="dash", color="red"),
        row=2,
        col=1,
    )
    fig.add_shape(
        type="line",
        x0=kl.index.min(),
        x1=kl.index.max(),
        y0=30,
        y1=30,
        line=dict(dash="dash", color="green"),
        row=2,
        col=1,
    )

    # Update layout
    fig.update_layout(
        height=700,
        title_text="Close Price and RSI",
        xaxis_title="Date",
        yaxis_title="Price",
        yaxis2_title="RSI",
        hovermode="x unified",  # Show all hover data for the same x value
    )

    # Create a line chart for Final Balance
    balance_fig = {
        "data": [
            {
                "x": trades_df["exit_date"],
                "y": trades_df["final_balance"],
                "type": "line",
                "name": "Final Balance",
                "line": {"color": "orange"},
            },
        ],
        "layout": {
            "title": "Final Balance Over Time",
            "xaxis": {"title": "Exit Date"},
            "yaxis": {"title": "Final Balance"},
        },
    }

    return metrics_table, trades_table, pnl_fig, fig, balance_fig


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
