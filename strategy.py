import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from ta.volatility import BollingerBands


class Strategy:
    def __init__(self, strategy_name="sma_crossover", params=None):
        self.strategy_name = strategy_name
        self.params = params or {}

    def generate_signals(self, df: pd.DataFrame):
        """
        df: DataFrame con columnas: ['timestamp','open','high','low','close','volume']
        Retorna (signal, price):
            signal en ['long', 'short', 'flat']
            price el precio actual (usado como referencia de entrada)
        """
        if len(df) < 50:
            return "flat", None

        if self.strategy_name == "sma_crossover":
            return self.sma_crossover(df)
        elif self.strategy_name == "rsi":
            return self.rsi_strategy(df)
        elif self.strategy_name == "bollinger":
            return self.bollinger_band_breakout(df)
        else:
            return "flat", None

    def sma_crossover(self, df):
        short_window = self.params.get("short_window", 10)
        long_window = self.params.get("long_window", 30)

        sma_short = SMAIndicator(close=df["close"], window=short_window).sma_indicator()
        sma_long = SMAIndicator(close=df["close"], window=long_window).sma_indicator()

        # Señal en la última vela
        if (
            sma_short.iloc[-1] > sma_long.iloc[-1]
            and sma_short.iloc[-2] <= sma_long.iloc[-2]
        ):
            return "long", df["close"].iloc[-1]
        elif (
            sma_short.iloc[-1] < sma_long.iloc[-1]
            and sma_short.iloc[-2] >= sma_long.iloc[-2]
        ):
            return "short", df["close"].iloc[-1]
        else:
            return "flat", None

    def rsi_strategy(self, df):
        period = self.params.get("rsi_period", 14)
        rsi = RSIIndicator(close=df["close"], window=period).rsi()
        last_rsi = rsi.iloc[-1]

        if last_rsi < 30:
            return "long", df["close"].iloc[-1]
        elif last_rsi > 70:
            return "short", df["close"].iloc[-1]
        else:
            return "flat", None

    def bollinger_band_breakout(self, df):
        period = self.params.get("period", 20)
        multiplier = self.params.get("multiplier", 2)

        bb = BollingerBands(close=df["close"], window=period, window_dev=multiplier)
        upper = bb.bollinger_hband()
        lower = bb.bollinger_lband()

        last_close = df["close"].iloc[-1]
        prev_close = df["close"].iloc[-2]
        last_upper = upper.iloc[-1]
        last_lower = lower.iloc[-1]
        prev_upper = upper.iloc[-2]
        prev_lower = lower.iloc[-2]

        # Breakout alcista
        if last_close > last_upper and prev_close <= prev_upper:
            return "long", last_close
        # Breakout bajista
        elif last_close < last_lower and prev_close >= prev_lower:
            return "short", last_close
        else:
            return "flat", None
