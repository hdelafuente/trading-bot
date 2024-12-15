from time import sleep
from binance_integration import Binance
from utils import add_indicators, calculate_position_pnl
from strategy import Strategy


class TradingBot:
    def __init__(self, api_key, api_secret, leverage, risk_balance, max_positions):
        self.session = Binance(api_key, api_secret)
        self.leverage = leverage
        self.risk_balance = risk_balance
        self.max_positions = max_positions
        self.positions = []
        self.trades = []

    def look_for_signals(self, symbols, timeframe):
        signals = []
        for symbol in symbols:
            kl = self.fetch_klines_with_indicators(symbol, timeframe)
            sign = self.determine_signal(kl)
            if sign != "hold" and symbol not in self.positions:
                signals.append(self.create_signal(symbol, sign, kl))
                sleep(1)
        return signals

    def fetch_klines_with_indicators(self, symbol, timeframe):
        kl = self.session.klines(symbol, timeframe)
        add_indicators(kl)
        return kl

    def determine_signal(self, kl):
        return Strategy.zeus(kl)

    def create_signal(self, symbol, sign, kl):
        return {
            "symbol": symbol,
            "sign": sign,
            "entry_price": kl.Close.iloc[-1],
        }

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

    def backtest(self, symbol, timeframe, tp, sl, balance):
        trades = []
        in_position = False
        kl = self.session.klines(symbol, timeframe)
        add_indicators(kl)

        for i in range(3, len(kl)):
            kl_slice = kl.iloc[:i]
            sign = Strategy.zeus(kl_slice)
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
                else:
                    if (
                        kl_slice.Close.iloc[-1] <= trade["tp_price"]
                        or kl_slice.Close.iloc[-1] >= trade["sl_price"]
                    ):
                        trade["exit_date"] = kl_slice.index[-1]
                        trade["exit_price"] = kl_slice.Close.iloc[-1]
                        trade["open"] = False
                        in_position = False
            else:
                if sign != "hold":
                    trade = self.enter_trade(kl_slice, sign, tp, sl, balance)
                    trades.append(trade)
                    in_position = True

        if trades and trades[-1]["open"]:
            trades[-1]["exit_price"] = kl.Close.iloc[-1]
            trades[-1]["open"] = False
            trades[-1]["pnl"] = (
                (trades[-1]["exit_price"] - trades[-1]["entry_price"])
                * (trades[-1]["qty"] / trades[-1]["entry_price"])
                if trades[-1]["sign"] == "buy"
                else (trades[-1]["entry_price"] - trades[-1]["exit_price"])
                * (trades[-1]["qty"] / trades[-1]["entry_price"])
            )

        return trades

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
