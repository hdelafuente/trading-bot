from binance.um_futures import UMFutures
from binance.error import ClientError


class BinanceIntegration:
    def __init__(self, api_key, api_secret):
        self.client = UMFutures(key=api_key, secret=api_secret)

    def place_order(self, symbol, side, quantity):
        try:
            order = self.client.new_order(
                symbol=symbol, side=side, type="MARKET", quantity=quantity
            )
            return order
        except ClientError as e:
            print(f"Error placing order: {e}")
            return None

    def get_positions(self, symbol):
        try:
            positions = self.client.position_information(symbol=symbol)
            return positions
        except ClientError as e:
            print(f"Error fetching positions: {e}")
            return []

    def get_balance(self):
        try:
            balance = self.client.balance()
            return balance
        except ClientError as e:
            print(f"Error fetching balance: {e}")
            return []
