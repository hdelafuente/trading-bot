import os
import time
import pprint as pp
from datetime import datetime
from strategy import Strategy
from data_fetcher import DataFetcher
from binance_integration import BinanceIntegration
from backtester import Backtester
import sys
import json

DEBUG_MODE = os.environ.get("DEBUG_MODE", "True") == "True"


def run_bot(symbol="BTCUSDT", interval="30m", strategy_name="sma_crossover"):
    params = {}
    if strategy_name == "sma_crossover":
        params = {"short_window": 10, "long_window": 30}
    elif strategy_name == "rsi":
        params = {"rsi_period": 14}
    elif strategy_name == "bollinger":
        params = {"period": 20, "multiplier": 2}

    strat = Strategy(strategy_name=strategy_name, params=params)
    dfetch = DataFetcher(symbol=symbol, interval=interval)

    # Colocar tus claves reales
    API_KEY = os.environ.get("API_KEY")
    API_SECRET = os.environ.get("API_SECRET")

    binance_client = BinanceIntegration(API_KEY, API_SECRET)

    quantity = 0.001

    while True:
        df = dfetch.fetch_klines(limit=100)
        signal, entry_price = strat.generate_signals(df)

        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"[{current_time}] Signal: {signal}, Price: {entry_price}, DEBUG_MODE={DEBUG_MODE}"
        )

        # Tomar acción (si no estamos en debug)
        if not DEBUG_MODE and signal in ["long", "short"]:
            side = "BUY" if signal == "long" else "SELL"
            order = binance_client.place_order(symbol, side, quantity)
            if order:
                print(f"Order placed: {order}")
            else:
                print("Failed to place order.")

        # Esperar 5 minutos
        time.sleep(300)


def run_backtest(
    symbol="BTCUSDT",
    interval="30m",
    strategy_name="sma_crossover",
    stop_loss=0.02,
    take_profit=0.04,
    initial_capital=1000,
    qty=0.01,
):
    params = {}
    if strategy_name == "sma_crossover":
        params = {"short_window": 10, "long_window": 30}
    elif strategy_name == "rsi":
        params = {"rsi_period": 14}
    elif strategy_name == "bollinger":
        params = {"period": 20, "multiplier": 2}

    strat = Strategy(strategy_name=strategy_name, params=params)
    dfetch = DataFetcher(symbol=symbol, interval=interval)
    df = dfetch.fetch_klines(limit=1000)

    bt = Backtester(
        strategy=strat,
        stop_loss_pct=stop_loss,
        take_profit_pct=take_profit,
        initial_capital=initial_capital,
        qty=qty,
    )
    results = bt.run_backtest(df)

    # Add initial capital to results
    results["initial_capital"] = initial_capital

    # Save results to a JSON file
    with open("backtest_results.json", "w") as f:
        json.dump(results, f, indent=4)

    print("Backtest Results:")
    pp.pprint(results)


if __name__ == "__main__":
    # Comandos:
    # python main.py run_bot
    # python main.py run_backtest

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        symbol = os.environ.get("SYMBOL", "BTCUSDT")
        interval = os.environ.get("INTERVAL", "30m")
        strategy_name = os.environ.get("STRATEGY_NAME", "sma_crossover")

        if mode == "run_bot":
            run_bot(symbol=symbol, interval=interval, strategy_name=strategy_name)
        elif mode == "run_backtest":
            stop_loss = float(os.environ.get("STOP_LOSS", "0.02"))
            take_profit = float(os.environ.get("TAKE_PROFIT", "0.04"))
            initial_capital = float(os.environ.get("INITIAL_CAPITAL", "1000"))
            qty = float(os.environ.get("QTY", "0.01"))
            run_backtest(
                symbol=symbol,
                interval=interval,
                strategy_name=strategy_name,
                stop_loss=stop_loss,
                take_profit=take_profit,
                initial_capital=initial_capital,
                qty=qty,
            )
        else:
            print("Modo no soportado. Use 'run_bot' o 'run_backtest'.")
    else:
        print("Por favor, especifique el modo: run_bot o run_backtest")
