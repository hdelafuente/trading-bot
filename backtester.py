import pandas as pd
import numpy as np


class Backtester:
    def __init__(
        self,
        strategy,
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
        initial_capital=1000,
        qty=0.01,
    ):
        """
        stop_loss_pct: Ej. 0.02 = 2%
        take_profit_pct: Ej. 0.04 = 4%
        initial_capital: Capital inicial
        qty: cantidad (en este ejemplo simplificado)
        """
        self.strategy = strategy
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.initial_capital = initial_capital
        self.qty = qty

    def run_backtest(self, df: pd.DataFrame):
        df = df.copy()

        # Generate signals
        df["signal"], df["entry_signal_price"] = zip(
            *df.apply(
                lambda row: self.strategy.generate_signals(df.loc[: row.name]), axis=1
            )
        )

        position = None
        entry_price = 0
        entry_timestamp = None  # Track the entry timestamp
        capital = self.initial_capital
        trades = []

        for i in range(1, len(df)):
            signal = df["signal"].iloc[i]
            close_price = df["close"].iloc[i]
            timestamp = df["timestamp"].iloc[i]  # Get the timestamp

            if position is None:
                # No open position, wait for signal
                if signal == "long":
                    position = "long"
                    entry_price = close_price
                    entry_timestamp = timestamp  # Record the entry timestamp
                    # Calculate SL and TP
                    stop_loss_price = entry_price * (1 - self.stop_loss_pct)
                    take_profit_price = entry_price * (1 + self.take_profit_pct)
                elif signal == "short":
                    position = "short"
                    entry_price = close_price
                    entry_timestamp = timestamp  # Record the entry timestamp
                    stop_loss_price = entry_price * (1 + self.stop_loss_pct)
                    take_profit_price = entry_price * (1 - self.take_profit_pct)
            else:
                # Position is open, check if SL, TP, or opposite signal is triggered
                if position == "long":
                    # Check SL/TP
                    if (
                        close_price <= stop_loss_price
                        or close_price >= take_profit_price
                        or signal == "short"
                    ):
                        # Close long
                        profit = (close_price - entry_price) * (self.qty)
                        capital += profit
                        trades.append(
                            {
                                "profit": profit,
                                "entry_timestamp": entry_timestamp,
                                "exit_timestamp": timestamp,
                                "balance_after_trade": capital,  # Add balance after trade
                            }
                        )
                        # If opposite signal, open new short position
                        if signal == "short":
                            position = "short"
                            entry_price = close_price
                            entry_timestamp = (
                                timestamp  # Record the new entry timestamp
                            )
                            stop_loss_price = entry_price * (1 + self.stop_loss_pct)
                            take_profit_price = entry_price * (1 - self.take_profit_pct)
                        else:
                            position = None
                else:  # position == 'short'
                    if (
                        close_price >= stop_loss_price
                        or close_price <= take_profit_price
                        or signal == "long"
                    ):
                        # Close short
                        profit = (entry_price - close_price) * (self.qty)
                        capital += profit
                        trades.append(
                            {
                                "profit": profit,
                                "entry_timestamp": entry_timestamp,
                                "exit_timestamp": timestamp,
                                "balance_after_trade": capital,  # Add balance after trade
                            }
                        )
                        # If opposite signal, open new long position
                        if signal == "long":
                            position = "long"
                            entry_price = close_price
                            entry_timestamp = (
                                timestamp  # Record the new entry timestamp
                            )
                            stop_loss_price = entry_price * (1 - self.stop_loss_pct)
                            take_profit_price = entry_price * (1 + self.take_profit_pct)
                        else:
                            position = None

        # If there's an open position at the end, close it at the last price
        if position is not None:
            final_price = df["close"].iloc[-1]
            final_timestamp = df["timestamp"].iloc[-1]
            if position == "long":
                profit = (final_price - entry_price) * (self.qty)
            else:
                profit = (entry_price - final_price) * (self.qty)
            capital += profit
            trades.append(
                {
                    "profit": profit,
                    "entry_timestamp": entry_timestamp,
                    "exit_timestamp": final_timestamp,
                    "balance_after_trade": capital,
                    "entry_signal_price": entry_price,
                    "exit_signal_price": final_price,
                }
            )

        return {
            "final_capital": capital,
            "trades": trades,
            "win_rate": (
                np.mean([1 if t["profit"] > 0 else 0 for t in trades]) if trades else 0
            ),
            "total_trades": len(trades),
        }

    def calculate_metrics(self, trades, initial_capital):
        total_profit = sum(t["profit"] for t in trades)
        winning_trades = [t for t in trades if t["profit"] > 0]
        losing_trades = [t for t in trades if t["profit"] < 0]

        win_ratio = len(winning_trades) / len(trades) if trades else 0
        profit_factor = (
            sum(t["profit"] for t in winning_trades)
            / abs(sum(t["profit"] for t in losing_trades))
            if losing_trades
            else float("inf")
        )
        roi = (total_profit / initial_capital) * 100
        max_drawdown = self.calculate_max_drawdown(trades, initial_capital)
        avg_profit = (
            sum(t["profit"] for t in winning_trades) / len(winning_trades)
            if winning_trades
            else 0
        )
        avg_loss = (
            sum(t["profit"] for t in losing_trades) / len(losing_trades)
            if losing_trades
            else 0
        )

        return {
            "win_ratio": win_ratio,
            "profit_factor": profit_factor,
            "roi": roi,
            "max_drawdown": max_drawdown,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
        }

    def calculate_max_drawdown(self, trades, initial_capital):
        peak = initial_capital
        max_drawdown = 0
        capital = initial_capital

        for trade in trades:
            capital += trade["profit"]
            if capital > peak:
                peak = capital
            drawdown = (peak - capital) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown
