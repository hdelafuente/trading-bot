from time import sleep
from binance_integration import Binance
from utils import add_indicators, calculate_position_pnl
from strategy import Strategy
from metrics import Metrics
import json
import pandas as pd


class TradingBot:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        leverage: int,
        risk_balance: float,
        max_positions: int = 1,
        selected_strategy: str = "stoch_rsi_ema_200",
    ):
        self.session = Binance(api_key, api_secret)
        self.strategy = Strategy()
        self.metrics = Metrics()
        self.leverage = leverage
        self.risk_balance = risk_balance
        self.max_positions = max_positions
        self.positions = list()
        self.trades = list()
        self.selected_strategy = selected_strategy
        self.kl = dict()

    """
    Data Functions
    """

    def fetch_kline(self, symbol, timeframe):
        kl = pd.read_csv(f"data/{symbol}-{timeframe}.csv")
        kl["Time"] = pd.to_datetime(kl["Time"])
        kl.set_index("Time", inplace=True)
        return kl.tail(5000)

    def fetch_klines(self, symbols, timeframe):
        for symbol in symbols:
            self.kl[symbol] = self.fetch_kline(symbol, timeframe)

    def add_signals(self, strategy):
        window = 20
        for symbol, klines in self.kl.items():
            print(f"Adding signals for {strategy} on {symbol}")

            # Pre-calculate necessary columns for signal determination
            signals = []
            signal_prices = []

            for i in range(window, len(klines)):
                kl_slice = klines.iloc[i - window : i]
                sign = self.strategy.get_signal(kl_slice)
                signals.append(sign)
                signal_prices.append(
                    kl_slice.Close.iloc[-1] if sign != "hold" else None
                )

            # Assign the calculated signals and prices to the DataFrame
            self.kl[symbol][f"{strategy}_signal"] = [None] * window + signals
            self.kl[symbol][f"{strategy}_signal_price"] = [
                None
            ] * window + signal_prices

    def create_signal(self, symbol, sign, kl):
        return {
            "symbol": symbol,
            "sign": sign,
            "entry_price": kl.Close.iloc[-1],
        }

    """
    Bot Functions
    """

    def look_for_signals(self, symbols, timeframe):
        signals = []
        for symbol in symbols:
            kl = self.fetch_kline(symbol, timeframe)
            sign = self.strategy.get_signal(kl)
            if sign != "hold" and symbol not in self.positions:
                signals.append(self.create_signal(symbol, sign, kl))
                sleep(1)
        return signals

    def open_real_position(self, symbol, sign, qty, mode, tp, sl):
        entry_price, tp_price, sl_price = self.session.open_order_market(
            symbol, sign, qty, self.leverage, mode, tp, sl
        )
        lended_qty = qty / entry_price
        position = {
            "entry_price": entry_price,
            "tp_price": tp_price,
            "sl_price": sl_price,
            "lended_qty": lended_qty,
            "sign": sign,
        }
        self.positions.append(position)
        return position

    def update_positions_pnl(self):
        for position in self.positions:
            last_close = self.session.get_ticker_usdt(position["symbol"])
            pnl = calculate_position_pnl(position, last_close)
            position["pnl"] = pnl

    def enter_trade(self, entry_date, entry_price, sign, tp, sl, balance):
        trade = {
            "entry_date": entry_date,
            "exit_date": None,
            "entry_price": entry_price,
            "exit_price": 0,
            "qty": balance * self.leverage * self.risk_balance,
            "sign": sign,
            "open": True,
        }
        if sign == "buy":
            trade["tp_price"] = entry_price * (1 + tp)
            trade["sl_price"] = entry_price * (1 - sl)
        else:
            trade["tp_price"] = entry_price * (1 - tp)
            trade["sl_price"] = entry_price * (1 + sl)
        return trade

    """
    Backtest Functions
    """

    def backtest_strategy(self, symbol, tp, sl, balance, strategy):
        trades = []
        in_position = False
        updated_balance = balance

        for i in range(3, len(self.kl[symbol])):
            kl_slice = self.kl[symbol].iloc[:i]
            sign = kl_slice[f"{strategy}_signal"].iloc[-1]
            if in_position:
                trade = trades[-1]
                if trade["sign"] == "buy":
                    if (
                        kl_slice.Close.iloc[-1] >= trade["tp_price"]
                        or kl_slice.Close.iloc[-1] <= trade["sl_price"]
                    ):
                        trade["exit_date"] = kl_slice.index[-1]
                        trade["exit_price"] = kl_slice.Close.iloc[-1]
                        trade["open"] = False
                        in_position = False
                        trade["pnl"] = calculate_position_pnl(
                            trade, kl_slice.Close.iloc[-1]
                        )
                        trade["final_balance"] = (
                            trade["starting_balance"] + trade["pnl"]
                        )
                        updated_balance = trade["final_balance"]
                else:
                    if (
                        kl_slice.Close.iloc[-1] <= trade["tp_price"]
                        or kl_slice.Close.iloc[-1] >= trade["sl_price"]
                    ):
                        trade["exit_date"] = kl_slice.index[-1]
                        trade["exit_price"] = kl_slice.Close.iloc[-1]
                        trade["open"] = False
                        in_position = False
                        trade["pnl"] = calculate_position_pnl(
                            trade, kl_slice.Close.iloc[-1]
                        )
                        trade["final_balance"] = (
                            trade["starting_balance"] + trade["pnl"]
                        )
                        updated_balance = trade["final_balance"]

            else:
                if sign != "hold":
                    trade = self.enter_trade(
                        kl_slice.index[-1],
                        kl_slice.Close.iloc[-1],
                        sign,
                        tp,
                        sl,
                        updated_balance,
                    )
                    trade["starting_balance"] = updated_balance
                    trade["lended_qty"] = trade["qty"] / trade["entry_price"]
                    trade["pnl"] = calculate_position_pnl(
                        trade, kl_slice.Close.iloc[-1]
                    )
                    updated_balance -= trade["starting_balance"] * self.risk_balance
                    trades.append(trade)
                    in_position = True

        if trades and trades[-1]["open"]:
            trades[-1]["exit_price"] = self.kl[symbol].Close.iloc[-1]
            trades[-1]["pnl"] = calculate_position_pnl(
                trades[-1], self.kl[symbol].Close.iloc[-1]
            )
            trades[-1]["starting_balance"] = updated_balance
            updated_balance = updated_balance + trades[-1]["pnl"]
            trades[-1]["final_balance"] = updated_balance
        return trades

    def write_backtest_results(
        self,
        strategy,
        symbol,
        timeframe,
        tp,
        sl,
        balance,
        trades,
        metrics,
    ):
        config = {
            "symbol": symbol,
            "timeframe": timeframe,
            "tp": tp,
            "sl": sl,
            "leverage": self.leverage,
            "balance": balance,
            "risk_balance": self.risk_balance,
        }
        result = {"metrics": metrics, "trades": trades, "config": config}

        # Save result to a JSON file
        with open(f"results/{strategy}_backtest_results_{symbol}.json", "w") as f:
            json.dump(result, f, indent=4)

    def backtest(self, symbols, timeframe, tp, sl, balance, strategy):
        for symbol in symbols:
            trades = self.backtest_strategy(symbol, tp, sl, balance, strategy)
            metrics = self.metrics.calculate_metrics(trades, balance)
            for trade in trades:
                if isinstance(trade.get("exit_date"), pd.Timestamp):
                    trade["exit_date"] = trade["exit_date"].isoformat()

                if isinstance(trade.get("entry_date"), pd.Timestamp):
                    trade["entry_date"] = trade["entry_date"].isoformat()
            self.write_backtest_results(
                strategy, symbol, timeframe, tp, sl, balance, trades, metrics
            )
