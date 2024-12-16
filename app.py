import dash
from dash import dcc, html, dash_table
import pandas as pd
import json
from dash.dependencies import Input, Output
from bot import TradingBot
from utils import API_KEY, API_SECRET, SYMBOLS


# Load backtest results from JSON files
def load_backtest_results(symbols):
    results = []
    for symbol in symbols:
        with open(f"results/backtest_results_{symbol}.json", "r") as f:
            result = json.load(f)
            result["symbol"] = symbol
            results.append(result)
    return results


# Prepare data for the Dash app
symbols = SYMBOLS
backtest_results = load_backtest_results(symbols)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div(
    [
        html.H1("Backtest Results"),
        dcc.Dropdown(
            id="symbol-dropdown",
            options=[{"label": symbol, "value": symbol} for symbol in symbols],
            value=symbols[0],  # Default value
            style={"margin-bottom": "20px"},
        ),
        dcc.Loading(
            id="loading-metrics",
            type="circle",
            children=[
                html.Div(
                    id="metrics-table",
                    style={"margin-bottom": "20px"},
                ),
                html.Div(
                    id="trades-table",
                    style={"margin-bottom": "20px"},
                ),
                dcc.Graph(
                    id="pnl-bar-chart",
                    style={"margin-bottom": "20px"},
                ),
                dcc.Graph(
                    id="price-line-chart",
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
    ],
    [Input("symbol-dropdown", "value")],
)
def update_content(selected_symbol):
    # Instantiate TradingBot and fetch klines with indicators
    bot = TradingBot(
        api_key=API_KEY,
        api_secret=API_SECRET,
        leverage=10,
        risk_balance=0.3,
        max_positions=1,
    )
    kl = bot.fetch_klines_with_indicators(selected_symbol, "30m")

    # Filter results for the selected symbol
    selected_result = next(
        res for res in backtest_results if res["symbol"] == selected_symbol
    )
    metrics_df = pd.DataFrame([selected_result["metrics"]])
    trades_df = pd.DataFrame(selected_result["trades"])

    metrics_table = dash_table.DataTable(
        data=metrics_df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in metrics_df.columns],
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

    # Create a line chart for Close Price with trade markers
    price_fig = {
        "data": [
            {
                "x": kl.index,
                "y": kl["Close"],
                "type": "line",
                "name": "Close Price",
            },
            {
                "x": winning_trades["entry_date"],
                "y": winning_trades["entry_price"],
                "mode": "markers",
                "name": "Winning Trade Open",
                "marker": {"color": "green", "size": 10},
            },
            {
                "x": winning_trades["exit_date"],
                "y": winning_trades["exit_price"],
                "mode": "markers",
                "name": "Winning Trade Close",
                "marker": {"color": "green", "size": 10, "symbol": "x"},
            },
            {
                "x": losing_trades["entry_date"],
                "y": losing_trades["entry_price"],
                "mode": "markers",
                "name": "Losing Trade Open",
                "marker": {"color": "red", "size": 10},
            },
            {
                "x": losing_trades["exit_date"],
                "y": losing_trades["exit_price"],
                "mode": "markers",
                "name": "Losing Trade Close",
                "marker": {"color": "red", "size": 10, "symbol": "x"},
            },
        ],
        "layout": {
            "title": "Close Price with Trade Markers",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Price"},
        },
    }

    return metrics_table, trades_table, pnl_fig, price_fig


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
