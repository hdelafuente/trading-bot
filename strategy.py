class Strategy:

    def available_strategies(self):
        return ["zeus", "ichimoku_cloud_with_confirmation", "stoch_rsi_ema_200"]

    def get_signal(self, data, strategy_name):
        if strategy_name == "zeus":
            return self.zeus(data)
        elif strategy_name == "ichimoku_cloud_with_confirmation":
            return self.ichimoku_cloud_with_confirmation(data)
        elif strategy_name == "stoch_rsi_ema_200":
            return self.stoch_rsi_ema_200(data)

    def zeus(self, data):
        actual_close = data.Close.iloc[-1]
        prev_close = data.Close.iloc[-2]

        actual_macd = data.macd.iloc[-1]
        actual_macd_signal = data.macd_signal.iloc[-1]
        actual_macd_diff = data.macd_diff.iloc[-1]

        prev_macd = data.macd.iloc[-2]
        prev_macd_signal = data.macd_signal.iloc[-2]
        prev_macd_diff = data.macd_diff.iloc[-2]

        macd_long_entry_signal = (
            actual_macd < 0
            and actual_macd > actual_macd_signal
            and prev_macd <= prev_macd_signal
            and prev_macd_diff < actual_macd_diff
        )
        macd_short_entry_signal = (
            actual_macd > 0
            and actual_macd < actual_macd_signal
            and prev_macd >= prev_macd_signal
            and prev_macd_diff > actual_macd_diff
        )

        bb_upper = data.bb_upper.iloc[-1]
        bb_lower = data.bb_lower.iloc[-1]
        bb_mid = data.bb_mid.iloc[-1]

        distance_to_upper = (actual_close - bb_upper) / bb_upper
        distance_to_lower = (actual_close - bb_lower) / bb_lower
        distance_to_mid = (actual_close - bb_mid) / bb_mid

        bb_long_entry_signal = actual_close < bb_mid and distance_to_lower <= 0.05
        bb_short_entry_signal = actual_close > bb_mid and distance_to_upper <= 0.05

        actual_rsi = data.rsi.iloc[-1]

        if macd_long_entry_signal and bb_long_entry_signal:
            return "buy"
        elif macd_short_entry_signal and bb_short_entry_signal:
            return "sell"
        else:
            return "hold"

    def ichimoku_cloud_with_confirmation(self, data):
        if (
            data.senkou_span_a.iloc[-1] > data.senkou_span_b.iloc[-1]
            and data.Close.iloc[-1] > data.tenkan_sen.iloc[-1]
            and data.Close.iloc[-1] > data.kijun_sen.iloc[-1]
            and data.Close.iloc[-1] > data.senkou_span_a.iloc[-1]
            and data.Close.iloc[-1] > data.senkou_span_b.iloc[-1]
            and data.rsi.iloc[-1] > 50  # Confirmación de RSI por encima de 50
        ):
            return "buy"
        elif (
            data.senkou_span_a.iloc[-1] < data.senkou_span_b.iloc[-1]
            and data.Close.iloc[-1] < data.tenkan_sen.iloc[-1]
            and data.Close.iloc[-1] < data.kijun_sen.iloc[-1]
            and data.Close.iloc[-1] < data.senkou_span_a.iloc[-1]
            and data.Close.iloc[-1] < data.senkou_span_b.iloc[-1]
            and data.rsi.iloc[-1] < 50  # Confirmación de RSI por debajo de 50
        ):
            return "sell"
        else:
            return "hold"

    def stoch_rsi_ema_200(self, data):
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
