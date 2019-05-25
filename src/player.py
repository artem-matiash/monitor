import pandas as pd
import numpy as np
from position import Position


class Player:
    def __init__(self, tradelog_df, data_df, base):
        self.tradelog_df = tradelog_df
        self.data_df = data_df
        self.base = base

    def generate_equity_curve(self):
        # Take ticker
        self.ticker = self.tradelog_df['ticker'].unique()
        assert len(self.ticker) == 1
        self.ticker = self.ticker[0]
        # Append df
        self.data_df = self.data_df[['price']]
        self.data_df['type'] = 'MTM'
        self.tradelog_df['type'] = 'TRADE'
        self.union_df = self.tradelog_df.append(self.data_df).sort_values(by=['timestamp', 'type'], ascending=[True, False])
        # Init position
        position = None
        # Iterate over union_df
        for it, row in self.union_df.iterrows():
            if row['type'] == 'TRADE':
                if position is None:
                    position = Position(it, self.ticker, self.base)
                position.trade(
                    it,
                    row['side'],
                    row['size'],
                    row['price'],
                    row['commission']
                )
            elif row['type'] == 'MTM':
                position.mark_to_market(
                    it,
                    row['price']
                )
            else:
                raise NotImplementedError
        logs = pd.DataFrame(position.logs).T
        return logs
