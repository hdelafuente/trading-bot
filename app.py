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
    STRATEGY,
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
    [Input("symbol-dropdown", "value")],
)
def update_content(selected_symbol: str):
    # Instantiate TradingBot and fetch klines with indicators
    backtest_results = load_backtest_results(STRATEGY, selected_symbol)
    kl = bot.fetch_kline(selected_symbol, TIMEFRAME)

    if len(backtest_results["trades"]) > 0:
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

        # Create a subplot figure with 2 rows, setting the row heights
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("Close Price", "MACD", "Stoch RSI"),
            row_heights=[
                0.7,
                0.3,
                0.3,
            ],  # 70% for the first row, 30% for the second row
        )

        # Use only the last 1000 rows for plotting
        plot_kl = kl.tail(1000)

        # Match entry prices from trades_df to klines dataframe
        plot_kl = plot_kl.copy()
        plot_kl["buy_entry_price"] = None
        plot_kl["sell_entry_price"] = None
        plot_kl["buy_exit_price"] = None
        plot_kl["sell_exit_price"] = None

        # Add entry prices
        for date, price, sign in zip(
            trades_df["entry_date"], trades_df["entry_price"], trades_df["sign"]
        ):
            if date in plot_kl.index:
                plot_kl.loc[date, f"{sign}_entry_price"] = price

        # Add exit prices
        for date, price, sign in zip(
            trades_df["exit_date"], trades_df["exit_price"], trades_df["sign"]
        ):
            if date in plot_kl.index:
                plot_kl.loc[date, f"{sign}_exit_price"] = price

        # Add Close Price and EMA 200 to the first row
        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["Close"],
                mode="lines",
                name="Close Price",
                hovertemplate="Date: %{x}<br>Close Price: %{y}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["ema_200"],
                mode="lines",
                name="EMA 200",
                line=dict(dash="dash", color="blue"),
                hovertemplate="Date: %{x}<br>EMA 200: %{y}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # Add trade markers to the first row
        # Add buy signals
        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["buy_entry_price"],
                mode="markers",
                name="Open Long",
                marker=dict(color="green", size=10, symbol="triangle-up"),
                hovertemplate="Date: %{x}<br>Open Long: %{y}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["buy_exit_price"],
                mode="markers",
                name="Close Long",
                marker=dict(color="green", size=10, symbol="triangle-down"),
                hovertemplate="Date: %{x}<br>Exit Long: %{y}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # Add sell signals
        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["sell_entry_price"],
                mode="markers",
                name="Open Short",
                marker=dict(color="red", size=10, symbol="triangle-down"),
                hovertemplate="Date: %{x}<br>Open Short: %{y}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["sell_exit_price"],
                mode="markers",
                name="Close Short",
                marker=dict(color="red", size=10, symbol="triangle-up"),
                hovertemplate="Date: %{x}<br>Exit Short: %{y}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        # Add second row
        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["macd"],
                mode="lines",
                name="MACD",
                line=dict(color="orange"),
                hovertemplate="Date: %{x}<br>MACD: %{y}<extra></extra>",
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["macd_signal"],
                mode="lines",
                name="MACD Signal",
                line=dict(color="blue"),
                hovertemplate="Date: %{x}<br>MACD Signal: %{y}<extra></extra>",
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Bar(
                x=plot_kl.index,
                y=plot_kl["macd_diff"],
                name="MACD Hist",
                marker=dict(
                    color=[
                        "red" if val < 0 else "green" for val in plot_kl["macd_diff"]
                    ]
                ),
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["stoch_rsi_k"],
                name="Stoch RSI K",
                line=dict(color="orange"),
            ),
            row=3,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=plot_kl.index,
                y=plot_kl["stoch_rsi_d"],
                name="Stoch RSI D",
                line=dict(color="blue"),
            ),
            row=3,
            col=1,
        )

        # Update layout
        fig.update_layout(
            height=700,
            title_text="Close Price",
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
    else:
        return None, None, None, None, None


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
