import sys
import json
import pandas as pd
from time import sleep
from utils import (
    API_KEY,
    API_SECRET,
    SYMBOLS,
    TIMEFRAME,
    TP,
    SL,
    LEVERAGE,
    RISK_BALANCE,
    BALANCE,
)
from bot import TradingBot
from metrics import Metrics


def run(
    bot: TradingBot,
    symbols: list,
    timeframe: str,
    tp: float,
    sl: float,
):
    mode = "ISOLATED"

    while True:
        try:
            balance = bot.session.get_balance_usdt()
            positions = bot.session.get_positions()
            orders = bot.session.check_orders()
            qty = balance * bot.leverage * bot.risk_balance

            for elem in orders:
                if elem["symbol"] not in [pos["symbol"] for pos in positions]:
                    bot.session.close_open_orders(elem["symbol"])

            print(f"Balance: {round(balance, 3)} USDT")
            print(f"{len(positions)} Positions: {[pos['symbol'] for pos in positions]}")
            bot.update_positions_pnl()

            for pos in positions:
                print(
                    f"{pos['symbol']} ({pos['sign']}) entry: $ {pos['entry_price']} USDT  PnL: $ {pos['pnl']} USDT"
                )

            if len(positions) < bot.max_positions:
                print("Looking for signals...")
                signals = bot.look_for_signals(symbols, timeframe)
                if signals:
                    for signal in signals:
                        bot.open_real_position(
                            signal["symbol"], signal["sign"], qty, mode, tp, sl
                        )
                        if len(positions) >= bot.max_positions:
                            break

            wait = 60 * 2
            print(f"Waiting {wait} sec")
            sleep(wait)
        except Exception as err:
            print(err)
            sleep(30)
        except KeyboardInterrupt:
            print("Finishing...")
            df = pd.DataFrame(bot.trades)
            print(df)
            break


def backtest(
    bot: TradingBot,
    symbol: str,
    timeframe: str,
    tp: float,
    sl: float,
    leverage: int,
    balance: float,
    risk_balance: float,
):
    print(f"Backtesting {symbol} on {timeframe} timeframe")
    trades = bot.backtest(symbol, timeframe, tp, sl, balance)
    metrics = Metrics().calculate_metrics(trades, balance)

    for trade in trades:
        if isinstance(trade.get("exit_date"), pd.Timestamp):
            trade["exit_date"] = trade["exit_date"].isoformat()

        if isinstance(trade.get("entry_date"), pd.Timestamp):
            trade["entry_date"] = trade["entry_date"].isoformat()

    config = {
        "symbol": symbol,
        "timeframe": timeframe,
        "tp": tp,
        "sl": sl,
        "leverage": leverage,
        "balance": balance,
        "risk_balance": risk_balance,
    }
    result = {"metrics": metrics, "trades": trades, "config": config}

    # Save result to a JSON file
    with open(f"results/backtest_results_{symbol}.json", "w") as f:
        json.dump(result, f, indent=4)

    return result


if __name__ == "__main__":

    if len(sys.argv) > 1:
        bot = TradingBot(API_KEY, API_SECRET, LEVERAGE, RISK_BALANCE, max_positions=3)
        if sys.argv[1] == "run":
            run(bot, SYMBOLS, TIMEFRAME, TP, SL)
        elif sys.argv[1] == "backtest":
            output = list()
            for symbol in SYMBOLS:
                metrics = backtest(
                    bot, symbol, TIMEFRAME, TP, SL, LEVERAGE, BALANCE, RISK_BALANCE
                )
                metrics["symbol"] = symbol
                output.append(metrics)
