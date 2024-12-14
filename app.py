import os
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from datetime import datetime
from data_fetcher import DataFetcher  # Import DataFetcher

# Load backtest results
with open("backtest_results.json", "r") as f:
    results = json.load(f)

# Convert trades to DataFrame
trades_df = pd.DataFrame(results["trades"])

# Convert timestamps to readable dates
trades_df["entry_date"] = trades_df["entry_timestamp"].apply(
    lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")
)
trades_df["exit_date"] = trades_df["exit_timestamp"].apply(
    lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")
)

# Fetch close prices using DataFetcher
data_fetcher = DataFetcher(symbol=os.getenv("SYMBOL"), interval=os.getenv("INTERVAL"))
price_df = data_fetcher.fetch_klines(limit=1000)

# Convert timestamps to readable dates for price data
price_df["date"] = price_df["timestamp"].apply(
    lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")
)

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Create metric cards using Bootstrap
metrics_cards = dbc.Row(
    [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Initial Capital", className="card-title"),
                        html.P(
                            f"${results['initial_capital']:,.2f}", className="card-text"
                        ),
                    ]
                )
            ),
            width=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Final Capital", className="card-title"),
                        html.P(
                            f"${results['final_capital']:,.2f}", className="card-text"
                        ),
                    ]
                )
            ),
            width=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Win Rate", className="card-title"),
                        html.P(
                            f"{results['win_rate'] * 100:.1f}%", className="card-text"
                        ),
                    ]
                )
            ),
            width=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Total Trades", className="card-title"),
                        html.P(f"{results['total_trades']}", className="card-text"),
                    ]
                )
            ),
            width=3,
        ),
    ],
    className="mb-4",
)

# Create the close price line chart with markers
close_price_fig = go.Figure()

# Add the line for close prices
close_price_fig.add_trace(
    go.Scatter(
        x=price_df["date"], y=price_df["close"], mode="lines", name="Close Price"
    )
)

close_price_fig.update_layout(
    title="Close Price Over Time with Trade Markers",
    xaxis_title="Date",
    yaxis_title="Close Price",
)

app.layout = dbc.Container(
    [
        html.H1("Backtest Results", className="my-4"),
        metrics_cards,
        dcc.Graph(
            id="trades-graph",
            figure=px.bar(
                trades_df,
                x="entry_date",
                y="profit",
                title="Trade Profits Over Time",
                labels={"entry_date": "Entry Date", "profit": "Profit"},
                hover_data=["exit_date"],
            ),
        ),
        dcc.Graph(
            id="balance-graph",
            figure=px.line(
                trades_df,
                x="exit_date",
                y="balance_after_trade",
                title="Balance Over Time",
                labels={"exit_date": "Exit Date", "balance_after_trade": "Balance"},
            ),
        ),
        dcc.Graph(
            id="close-price-graph",
            figure=close_price_fig,
        ),
    ],
    fluid=True,
)

if __name__ == "__main__":
    app.run_server(debug=True)
