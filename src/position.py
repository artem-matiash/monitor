from collections import OrderedDict
import pandas as pd

class Position:
    def __init__(
        self, timestamp, ticker, base
    ):
        self.timestamp = timestamp
        self.ticker = ticker
        self.base = base
        self.side = None
        self.size = 0
        self.price = None
        self.realised_pnl = 0
        self.unrealised_pnl = 0
        self.total_commission = 0
        self.equity = self.base + self.realised_pnl + self.unrealised_pnl - self.total_commission
        self.side_to_sign = {
            "SELL": -1,
            "BUY": 1
        }
        self.logs = OrderedDict()
        message = "INITIALIZATION"
        self._log(message)

    def mark_to_market(self, timestamp, new_price):
        self.unrealised_pnl = (new_price - self.price) * self.size * self.side_to_sign[self.side]
        self.timestamp = timestamp
        self.equity = self.base + self.unrealised_pnl + self.realised_pnl - self.total_commission
        message = "MTM"
        self._log(message)

    def trade(
        self, trade_timestamp, trade_side, trade_size,
        trade_price, trade_commission
    ):
        # logic: Trading Technologies
        self.timestamp = trade_timestamp
        self.total_commission += trade_commission
        # Screnario 0
        # INITIALIZE POSITION
        if self.side is None:
            message = "OPEN"
            self.side = trade_side
            self.size = trade_size
            self.price = trade_price
        # Scenario 1
        # RECEIVING NEW FILLS THAT INCREASE YOUR POSITION
        elif trade_side == self.side:
            message = "INCREASE"
            self.price = (self.price * self.size + trade_size * trade_price) / (self.size + trade_size)
            self.size += trade_size
        else:
            # Scenario 2
            # RECEIVING NEW FILLS THAT PARTIALLY DECREASE YOUR POSITION
            if trade_size < self.size:
                message = "DECREASE"
                self.realised_pnl += (trade_price - self.price) * trade_size * self.side_to_sign[self.side]
                self.size -= trade_size
                self.unrealised_pnl = (trade_price - self.price) * self.size * self.side_to_sign[self.side]
            # Scenario 3
            # RECEIVING FILLS THAT FLATTEN YOUR POSITION
            elif trade_size == self.size:
                message = "FLAT"
                self.realised_pnl += (trade_price - self.price) * trade_size * self.side_to_sign[self.side]
                self.size -= trade_size
                self.price = None
                self.side = None
                assert self.size == 0
                assert self.side is None
                assert self.price is None
                self.unrealised_pnl = 0
            # Scenario 4
            # RECEIVING FILLS THAT REVERSE YOUR POSITION
            else:
                message = "REVERSE"
                self.realised_pnl += (trade_price - self.price) * self.size * self.side_to_sign[self.side]
                self.price = trade_price
                self.size = abs(self.size - trade_size)
                self.side = trade_side
                self.unrealised_pnl = 0

        self.equity = self.base + self.unrealised_pnl + self.realised_pnl - self.total_commission
        self._log(message)

    def _log(self, message):
        stats = {
            "message": message,
            "unrealised_pnl": self.unrealised_pnl,
            "realised_pnl": self.realised_pnl,
            "total_commission": self.total_commission,
            "equity": self.equity,
            "base": self.base
        }
        self.logs[self.timestamp] = stats
