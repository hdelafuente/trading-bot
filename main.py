import sys
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
    STRATEGY,
    extract_data,
)
from bot import TradingBot


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
            print(
                f"{len(positions)} Positions: {[pos['symbol'] for pos in positions]}")
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


if __name__ == "__main__":

    if len(sys.argv) > 1:
        bot = TradingBot(
            API_KEY,
            API_SECRET,
            LEVERAGE,
            RISK_BALANCE,
            max_positions=3,
            selected_strategy=STRATEGY,
        )
        if sys.argv[1] == "run":
            run(bot, SYMBOLS, TIMEFRAME, TP, SL)
        elif sys.argv[1] == "extract":
            extract_data()
        elif sys.argv[1] == "backtest":
            print("Fetching klines...")
            bot.fetch_klines(SYMBOLS, TIMEFRAME)
            print(f"Backtesting {STRATEGY} on {SYMBOLS} ({TIMEFRAME})")
            bot.add_signals(STRATEGY)
            print("Running backtest...")
            bot.backtest(SYMBOLS, TIMEFRAME, TP, SL, BALANCE, STRATEGY)
