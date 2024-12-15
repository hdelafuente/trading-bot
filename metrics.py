import numpy as np


class Metrics:
    @staticmethod
    def calculate_metrics(trades, initial_balance):
        final_balance = initial_balance
        wins = []
        losses = []

        for trade in trades:
            trade_return = (
                (trade["exit_price"] - trade["entry_price"])
                * (trade["qty"] / trade["entry_price"])
                if trade["sign"] == "buy"
                else (trade["entry_price"] - trade["exit_price"])
                * (trade["qty"] / trade["entry_price"])
            )
            final_balance += trade_return
            trade["pnl"] = trade_return

            if trade_return > 0:
                wins.append(trade_return)
            else:
                losses.append(trade_return)

        win_ratio = len(wins) / len(trades) if trades else 0
        average_win = np.mean(wins) if wins else 0
        average_loss = np.mean(losses) if losses else 0
        risk_reward_ratio = -average_win / average_loss if average_loss else 0

        return {
            "initial_balance": round(initial_balance, 2),
            "final_balance": round(final_balance, 2),
            "win_ratio": round(win_ratio, 2),
            "average_win": round(average_win, 2),
            "average_loss": round(average_loss, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2),
        }
