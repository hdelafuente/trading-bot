class Strategy:

    def get_signal(self, data):
        if (
            data.stoch_rsi.iloc[-1] <= 20
            and data.ema_200.iloc[-1] < data.Close.iloc[-1]
        ):
            return "buy"
        elif (
            data.stoch_rsi.iloc[-1] >= 80
            and data.ema_200.iloc[-1] > data.Close.iloc[-1]
        ):
            return "sell"
        else:
            return "hold"
