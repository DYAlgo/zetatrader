#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import time
import datetime as dt
import pandas as pd
import numpy as np

from zetatrader.event import MarketEvent

class PriceData:
    """[summary]
    """
    def __init__(self, events, symbol_list, connection, barsize):
        self.events = events
        self.symbol_list = symbol_list
        self.connection = connection
        self.barsize = barsize
        self.continue_trading = True
        self.freq_dict = {
            '1MIN': 1, '5MIN': 5, '30MIN': 30, '1HOUR': 60, '4HOUR': 240 
            ,'1DAY' : 1440 
        }
        self.ticksize_dict = self.construct_ticksize_dict()
        self.symbol_data = self.construct_symbol_data()
    
    # ================================#
    # CONSTRUCTORS
    # ================================# 
    def construct_ticksize_dict(self):
        ticksize = {}
        for i in self.symbol_list:
            ticksize[i] = self.connection.get_symbol_info(
                i, False).get('tickSize')
            time.sleep(0.2)
        return ticksize

    def construct_symbol_data(self):
        px_dict = {}
        for i in self.symbol_list:
            px_dict[i] = pd.DataFrame(
                [[dt.datetime(2000,1,1), np.nan, np.nan, np.nan, np.nan, np.nan]]
                , columns=[
                    'price_date', 'open_price', 'high_price', 'low_price'
                    , 'close_price', 'volume'], index=[0])
        return px_dict

    # ================================#
    # PRICE HANDLER FUNCTIONS
    # ================================# 
    def retrive_price(self, ticker, n, freq=None):
        if freq == None:
            freq = self.freq_dict[self.barsize]
        price_data = self.connection.commandExecute(
            commandName = 'getChartRangeRequest',
            arguments={
                'info' : {
                    "period" : int(freq),
                    "start" : int(dt.datetime.now().timestamp()*1000), # Milli second CET time
                    "symbol" : ticker,
                    "ticks": -(n+500)
                } 
            }
        )
        if price_data.get('status') == True:
            price_data = pd.json_normalize(
                price_data.get('returnData').get('rateInfos')
            )
            tick_adj = self.ticksize_dict.get(ticker)
            if tick_adj != None and price_data.empty != True:
                # Adjust High, Low, and Close price
                price_data = price_data.iloc[-n:].reset_index(drop=True)
                price_data['high'] = price_data['open'] + price_data['high']
                price_data['low'] = price_data['open'] + price_data['low']
                price_data['close'] = price_data['open'] + price_data['close']
                # Mutliple them by ticksize adjustment factor
                price_data[['open', 'high', 'low','close']] = (
                    price_data[['open', 'high', 'low','close']] * tick_adj
                )
                # Convert ctm to datetime
                price_data['date'] = pd.to_datetime(
                    price_data['ctm'], unit='ms'
                )
                price_data.rename(
                    columns={"date": "price_date", "open": "open_price"
                        , 'high': 'high_price', 'low': 'low_price'
                        , 'close': 'close_price', 'vol': 'volume'
                    }
                    , inplace=True
                )
                return price_data[['price_date', 'open_price', 'high_price'
                    , 'low_price', 'close_price', 'volume']]
            else:
                if price_data.empty == True:
                    print('Data not available in date range.')
                    return pd.DataFrame()
                else:
                    raise ValueError('tickSize not found')
        else:
            self.connection._print(price_data)
            return pd.DataFrame()

    def get_latest_bar(self, symbol):
        """Return latest bar

        Args:
            symbol ([type]): [description]

        Returns:
            [type]: pandas series
        """
        bar = self.retrive_price(symbol, n=1)
        return bar

    def get_latest_bars(self, symbol, n):
        """Returns n most recent bar.

        Args:
            symbol ([type]): [description]
            n ([type]): [description]

        Returns:
            [type]: [description]
        """
        bar = self.retrive_price(symbol, n=n)
        return bar

    def get_latest_bar_value(self, symbol, val_type):
        """Returns specific field for latest bar
        """
        bar = self.get_latest_bar(symbol)
        return bar.loc[0, val_type]


    def get_latest_bar_values(self, symbol, val_type, n=1):
        """Returns specific field for the latest bars

        Args:
            symbol ([type]): [description]
            val_type ([type]): [description]
            n (int, optional): [description]. Defaults to 1.
        """
        bar = self.get_latest_bars(symbol, n=n)
        return bar.loc[:, val_type]

    def update_bars(self):
        """Updated bar index check for existence of next bar. Puts
        market event to queue if next bar is found. 
        """
        new_data = False
        for symbol in self.symbol_list:
            # Check if new data found
            bar = self.get_latest_bar(symbol)
            last_bar = self.symbol_data[symbol].loc[0, 'price_date']
            if last_bar < bar.loc[0, 'price_date']:
                # NEW DATA
                self.symbol_data[symbol].loc[0] = bar.loc[0]
                new_data = True
        if new_data == True:
            self.continue_trading = True
            self.events.put(MarketEvent()) 
        else:
            self.continue_trading = False


import os 
# Import Own Modules
from zetatrader.xtb.api import XRest
from zetatrader.event import OrderEvent

class DummieEvents:
    def __init__(self):
        self.items = []

    def put(self, x):
        self.items.append(x)

    def get(self):
        if self.items:
            return self.items.pop(0)

if __name__ == '__main__':
    demo_port = 5124
    client =  XRest(os.environ.get('XTB_DEMO_USER'), os.environ.get('XTB_DEMO_PW'))
    queue = DummieEvents()
    px_handler = PriceData(queue, ['EURUSD', 'ZINC'], client, '5MIN')
    px_handler.update_bars()
    eurusd = px_handler.get_latest_bar_values('AASSSS', 'close_price', 5)
    client.disconnect()