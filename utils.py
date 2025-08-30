import ta
import os
import json
import pandas as pd
from binance.client import Client

SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
]
TIMEFRAME = "1h"
TP = 0.05
SL = 0.02
LEVERAGE = 10
BALANCE = 300
RISK_BALANCE = 0.3
API_SECRET = os.environ.get("API_SECRET")
API_KEY = os.environ.get("API_KEY")


def load_backtest_results(symbol):
    with open(f"results/backtest_results_{symbol}.json", "r") as f:
        result = json.load(f)
        result["symbol"] = symbol
        return result


def add_indicators(data):

    # Skip indicators if they already exist in the data
    # if not "tenkan_sen" in data.columns:

    #     ichi = ta.trend.IchimokuIndicator(high=data.High, low=data.Low)
    #     data["tenkan_sen"] = ichi.ichimoku_base_line()
    #     data["kijun_sen"] = ichi.ichimoku_conversion_line()
    #     data["senkou_span_a"] = ichi.ichimoku_a()
    #     data["senkou_span_b"] = ichi.ichimoku_b()

    # data["rsi"] = ta.momentum.rsi(data.Close, window=14)
    # MACD
    macd = ta.trend.MACD(data.Close, window_fast=12,
                         window_slow=26, window_sign=9)
    data["macd"] = macd.macd()
    data["macd_diff"] = macd.macd_diff()
    data["macd_signal"] = macd.macd_signal()

    # RSI
    data["rsi"] = ta.momentum.rsi(data.Close, window=14)

    # Stoch RSI
    stoch_rsi = ta.momentum.StochRSIIndicator(data.Close, window=14)
    data["stoch_rsi"] = stoch_rsi.stochrsi()
    data["stoch_rsi_k"] = stoch_rsi.stochrsi_k()
    data["stoch_rsi_d"] = stoch_rsi.stochrsi_d()

    # Bandas de Bollinger
    indicator_bb = ta.volatility.BollingerBands(
        data.Close, window=20, window_dev=2)
    data["bb_upper"] = indicator_bb.bollinger_hband()
    data["bb_lower"] = indicator_bb.bollinger_lband()
    data["bb_mid"] = indicator_bb.bollinger_mavg()

    # # medias móviles exponenciales (EMA)
    # data["ema_8"] = ta.trend.ema_indicator(data.Close, window=8)
    # data["ema_20"] = ta.trend.ema_indicator(data.Close, window=20)
    # data["ema_50"] = ta.trend.ema_indicator(data.Close, window=50)
    # data["ema_100"] = ta.trend.ema_indicator(data.Close, window=100)
    data["ema_200"] = ta.trend.ema_indicator(data.Close, window=200)

    # ADX
    adx = ta.trend.ADXIndicator(data.High, data.Low, data.Close, window=14)
    data["adx"] = adx.adx()

    # Average true range
    # atr = ta.volatility.AverageTrueRange(data.High, data.Low, data.Close, window=14)
    # data["atr"] = atr.average_true_range()

    # Keltner Channel
    # keltner = ta.volatility.KeltnerChannel(
    #     data.High, data.Low, data.Close, window=20, window_atr=10
    # )
    # data["keltner_upper"] = keltner.keltner_channel_hband()
    # data["keltner_lower"] = keltner.keltner_channel_lband()

    # KST Indicator
    # kst = ta.trend.KSTIndicator(
    #     data.Close,
    #     roc1=10,
    #     roc2=15,
    #     roc3=20,
    #     roc4=30,
    #     window1=10,
    #     window2=10,
    #     window3=10,
    #     window4=15,
    #     nsig=9,
    # )
    # data["kst"] = kst.kst()
    # data["kst_diff"] = kst.kst_diff()
    # data["kst_sig"] = kst.kst_sig()

    # # ROC
    # roc = ta.momentum.ROCIndicator(data.Close, window=12)
    # data["roc"] = roc.roc()

    # Remove rows with null values in any column
    data.dropna(inplace=True)


def calculate_pnl_short(last_close, entry_price, lended_qty):
    pnl = (entry_price - last_close) * lended_qty
    return pnl


def calculate_pnl_long(last_close, entry_price, lended_qty):
    pnl = (last_close - entry_price) * lended_qty
    return pnl


def calculate_position_pnl(position, last_close):
    if position["sign"] == "buy":
        return calculate_pnl_long(
            last_close, position["entry_price"], position["lended_qty"]
        )
    else:
        return calculate_pnl_short(
            last_close, position["entry_price"], position["lended_qty"]
        )


def extract_data():
    client = Client(API_KEY, API_SECRET)
    for symbol in SYMBOLS:
        print(f"Extracting data for {symbol}...")
        try:
            inital_df = pd.read_csv(f"data/{symbol}-{TIMEFRAME}.csv")
        except FileNotFoundError:
            inital_df = pd.DataFrame(
                columns=["Time", "Open", "High", "Low", "Close", "Volume"]
            )

        inital_df["Time"] = pd.to_datetime(inital_df["Time"])
        start_date = (
            inital_df["Time"].iloc[-1].strftime("%Y-%m-%d %H:%M:%S")
            if len(inital_df) > 0
            else "2020-01-01 00:00:00"
        )

        klines = client.futures_historical_klines(
            symbol=symbol,
            interval=TIMEFRAME,
            start_str=start_date,
            limit=1000,
        )

        data = []
        for kline in klines:
            timestamp = pd.Timestamp(kline[0] / 1000, unit="s")
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            volume = float(kline[5])
            data.append(
                [timestamp, open_price, high_price, low_price, close_price, volume]
            )

        df = pd.DataFrame(
            data, columns=["Time", "Open", "High", "Low", "Close", "Volume"]
        )
        df = pd.concat([inital_df, df], ignore_index=True)
        add_indicators(df)
        df.to_csv(f"data/{symbol}-{TIMEFRAME}.csv", index=False)
        print(f"Data extracted")
