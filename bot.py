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
        selected_strategy: str = "ichimoku_cloud_with_confirmation",
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

    def fetch_klines_with_indicators(self, symbol, timeframe):
        kl = self.session.klines(symbol, timeframe)
        add_indicators(kl)
        return kl

    def fetch_klines(self, symbols, timeframe):
        for symbol in symbols:
            self.kl[symbol] = self.session.klines(symbol, timeframe)

    def determine_signal(self, kl, strategy):
        return self.strategy.get_signal(kl, strategy)

    def create_signal(self, symbol, sign, kl):
        return {
            "symbol": symbol,
            "sign": sign,
            "entry_price": kl.Close.iloc[-1],
        }

    def look_for_signals(self, symbols, timeframe):
        signals = []
        for symbol in symbols:
            kl = self.fetch_klines_with_indicators(symbol, timeframe)
            sign = self.determine_signal(kl, self.selected_strategy)
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

    def enter_trade(self, kl_slice, sign, tp, sl, balance):
        trade = {
            "entry_date": kl_slice.index[-1],
            "exit_date": None,
            "entry_price": kl_slice.Close.iloc[-1],
            "exit_price": 0,
            "qty": balance * self.leverage * self.risk_balance,
            "sign": sign,
            "open": True,
        }
        if sign == "buy":
            trade["tp_price"] = kl_slice.Close.iloc[-1] * (1 + tp)
            trade["sl_price"] = kl_slice.Close.iloc[-1] * (1 - sl)
        else:
            trade["tp_price"] = kl_slice.Close.iloc[-1] * (1 - tp)
            trade["sl_price"] = kl_slice.Close.iloc[-1] * (1 + sl)
        return trade

    def backtest_strategy(self, symbol, tp, sl, balance, strategy):
        trades = []
        in_position = False
        kl = self.kl[symbol]
        updated_balance = balance

        for i in range(3, len(kl)):
            kl_slice = kl.iloc[:i]
            sign = self.determine_signal(kl_slice, strategy)
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
                    trade = self.enter_trade(kl_slice, sign, tp, sl, updated_balance)
                    trade["starting_balance"] = updated_balance
                    trade["lended_qty"] = trade["qty"] / trade["entry_price"]
                    trade["pnl"] = calculate_position_pnl(
                        trade, kl_slice.Close.iloc[-1]
                    )
                    updated_balance -= trade["starting_balance"] * self.risk_balance
                    trades.append(trade)
                    in_position = True

        if trades and trades[-1]["open"]:
            trades[-1]["exit_price"] = kl.Close.iloc[-1]
            trades[-1]["open"] = False
            trades[-1]["pnl"] = calculate_position_pnl(trades[-1], kl.Close.iloc[-1])
            trades[-1]["starting_balance"] = updated_balance
            updated_balance = updated_balance + trades[-1]["pnl"]
            trades[-1]["final_balance"] = updated_balance
        return trades

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
