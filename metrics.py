import numpy as np


class Metrics:

    def calculate_metrics(self, trades, initial_balance):
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

        total_profit = sum(t["pnl"] for t in trades)
        roi = (total_profit / initial_balance) * 100

        max_drawdown = self.calculate_max_drawdown(trades, initial_balance)

        sum_pnl_win = sum(t["pnl"] for t in trades if t["pnl"] > 0)
        sum_pnl_loss = sum(t["pnl"] for t in trades if t["pnl"] < 0)
        profit_factor = sum_pnl_win / abs(sum_pnl_loss) if sum_pnl_loss != 0 else 0

        return {
            "initial_balance": round(initial_balance, 2),
            "final_balance": round(final_balance, 2),
            "win_ratio": round(win_ratio, 2),
            "average_win": round(average_win, 2),
            "average_loss": round(average_loss, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "roi": round(roi, 2),
            "max_drawdown": round(max_drawdown, 2),
            "profit_factor": round(profit_factor, 2),
        }

    def calculate_max_drawdown(self, trades, initial_balance):
        peak = initial_balance
        max_drawdown = 0
        capital = initial_balance

        for trade in trades:
            capital += trade["pnl"]
            if capital > peak:
                peak = capital
            drawdown = (peak - capital) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown
