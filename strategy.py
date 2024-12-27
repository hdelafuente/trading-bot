class Strategy:

    available_strategies = [
        "zeus",
        "ichimoku_cloud_with_confirmation",
        "stoch_rsi_ema_200",
    ]

    def get_signal(self, data, strategy_name):
        if strategy_name == "zeus":
            return self.zeus(data)
        elif strategy_name == "ichimoku_cloud_with_confirmation":
            return self.ichimoku_cloud_with_confirmation(data)
        elif strategy_name == "stoch_rsi_ema_200":
            return self.stoch_rsi_ema_200(data)

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

    def zeus(self, data):
        # MACD Calculation
        actual_macd = data.macd.iloc[-1]
        actual_macd_signal = data.macd_signal.iloc[-1]
        actual_macd_diff = data.macd_diff.iloc[-1]
        prev_macd_diff = data.macd_diff.iloc[-2]
        prev_macd = data.macd.iloc[-2]
        prev_macd_signal = data.macd_signal.iloc[-2]

        # Histogram (macd_diff) confirmation
        macd_diff_change = actual_macd_diff - prev_macd_diff
        macd_diff_mean = data.macd_diff.rolling(window=10).mean().iloc[-1]
        macd_diff_std = data.macd_diff.rolling(window=10).std().iloc[-1]

        # Check if histogram growth is significantly larger than usual
        histogram_confirm = macd_diff_change > (macd_diff_mean + 2 * macd_diff_std)

        macd_long_entry_signal = (
            actual_macd > actual_macd_signal
            and prev_macd <= prev_macd_signal
            and actual_macd_diff > 0
            and histogram_confirm  # Add histogram confirmation
        )
        macd_short_entry_signal = (
            actual_macd < actual_macd_signal
            and prev_macd >= prev_macd_signal
            and actual_macd_diff < 0
            and histogram_confirm  # Add histogram confirmation
        )

        # ADX
        adx = data.adx.iloc[-1]
        adx_rolling_mean = data.adx.rolling(window=20).mean().iloc[-1]
        adx_confirm = adx > adx_rolling_mean

        # Volume Confirmation
        actual_volume = data.Volume.iloc[-1]
        avg_volume = data.Volume.rolling(window=20).mean().iloc[-1]
        volume_confirm = actual_volume > avg_volume

        # Final Signal Decision
        if macd_long_entry_signal and adx_confirm and volume_confirm:
            return "buy"
        elif macd_short_entry_signal and adx_confirm and volume_confirm:
            return "sell"
        else:
            return "hold"
