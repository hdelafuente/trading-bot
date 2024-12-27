import os
import pandas as pd
from binance.client import Client
from utils import SYMBOLS, TIMEFRAME


# Configura tu clave API de Binance
API_SECRET = os.environ.get("API_SECRET")
API_KEY = os.environ.get("API_KEY")
client = Client(API_KEY, API_SECRET)
interval = Client.KLINE_INTERVAL_1HOUR  # Intervalo de tiempo diario

for symbol in SYMBOLS:
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
    print("Última fecha registrada : ", start_date)
    print("Cantiad de datos        : ", len(inital_df))

    end_date = pd.Timestamp.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )  # Fecha de fin (hasta hoy)

    klines = client.futures_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=start_date,
        limit=1000,
    )

    data = []
    for kline in klines:
        timestamp = pd.Timestamp(
            kline[0] / 1000, unit="s"
        )  # Convierte el timestamp a formato datetime
        open_price = float(kline[1])
        high_price = float(kline[2])
        low_price = float(kline[3])
        close_price = float(kline[4])
        volume = float(kline[5])
        data.append([timestamp, open_price, high_price, low_price, close_price, volume])

    df = pd.DataFrame(data, columns=["Time", "Open", "High", "Low", "Close", "Volume"])
    # concatenate initial_df with df
    df = pd.concat([inital_df, df], ignore_index=True)
    df.to_csv(f"data/{symbol}-{TIMEFRAME}.csv", index=False)
    print(f"Datos actualizados para {symbol}: {len(df)}")
