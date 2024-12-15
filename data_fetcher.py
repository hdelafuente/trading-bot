import requests
import pandas as pd


class DataFetcher:
    def __init__(self, symbol="BTCUSDT", interval="30m"):
        self.symbol = symbol
        self.interval = interval

    def fetch_klines(self, limit=100):
        # Datos de Futures
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={self.symbol}&interval={self.interval}&limit={limit}"
        data = requests.get(url).json()

        df = pd.DataFrame(
            data,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "qav",
                "num_trades",
                "taker_base_vol",
                "taker_quote_vol",
                "ignore",
            ],
        )
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms")
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        return df
