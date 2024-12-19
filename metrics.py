import numpy as np
import datetime as dt


class Metrics:

    def calculate_metrics(self, trades, initial_balance):
        wins = []
        losses = []

        for trade in trades:
            if trade["pnl"] > 0:
                wins.append(trade["pnl"])
            else:
                losses.append(trade["pnl"])

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

        start_date = f"{trades[0]['entry_date'].year}-{trades[0]['entry_date'].month}-{trades[0]['entry_date'].day}"

        if trades[-1]["exit_date"]:
            end_date = f"{trades[-1]['exit_date'].year}-{trades[-1]['exit_date'].month}-{trades[-1]['exit_date'].day}"
        else:
            end_date = f"{trades[-2]['exit_date'].year}-{trades[-2]['exit_date'].month}-{trades[-2]['exit_date'].day}"

        return {
            "initial_balance": round(initial_balance, 2),
            "final_balance": round(trades[-1]["final_balance"], 2),
            "win_ratio": round(win_ratio, 2),
            "average_win": round(average_win, 2),
            "average_loss": round(average_loss, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "roi": round(roi, 2),
            "max_drawdown": round(max_drawdown, 2),
            "profit_factor": round(profit_factor, 2),
            "start_date": start_date,
            "end_date": end_date,
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
