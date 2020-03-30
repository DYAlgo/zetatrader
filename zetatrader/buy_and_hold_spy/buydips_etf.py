#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# buy_and_hold.py

# This is a buy and hold strategy that simply buys on the first trading day
# and holds it forever. This is useful for comparing as a benchmark to other 
# strategies to 

from __future__ import print_function

# Add the trading infrastructure and backtest directory to path
import os
import datetime as dt
import pandas as pd
import time
# Import classes needed by the backtest 
from tradingframework.strategy.base import AbstractStrategy
from tradingframework.execution_handler.execution import BetterSimulatedExecutionHandler
from tradingframework.price_handler.sec_db_price_handler import SecDbPriceHandler
from tradingframework.portfolio.portfolio import Portfolio
from tradingframework.book.book import Book 
from tradingframework.money_management import MoneyManagement
from tradingframework.performance.trading_stats import TradingStats
from tradingframework.event import SignalEvent
from tradingframework.trading_session import TradingSession


class Buy_And_Hold_Dummie(AbstractStrategy):
    """
    This strategy simply goes long on a security from 
    the first day and sells it evert 100th market bar event.

    The intention of this strategy is to test the backtesting
    package.
    """
    def __init__(
        self, bars, events
    ):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events

        # Set to True if a symbol is in the market
        self.bought = self._calculate_initial_bought()
        self.bar_since_buy = 0


    def __str__(self):
        """
        Prints the name of this strategy
        """
        return "Buy and Hold Strategy"

    def _calculate_initial_bought(self):
        """
        Adds keys to the bought dictionary for all symbols
        and sets them to 'OUT'.
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought

    # def construct_signal_log(self):
    #     """
    #     This constructs a signal log for signal by signal 
    #     validation purpose
    #     """
    #     signal_log = pd.DataFrame(
    #         {'timestamp':[], 'symbol_id':[], 'direction':[], 
    #         'price':[], 'mode':[]}
    #     )

    #     signal_log = signal_log[['timestamp', 'symbol_id',
    #         'direction', 'price', 'mode']]

    #     return signal_log
    
    # def update_signal_log(self, signal, timestamp, price, mode):
    #     """
    #     Adds or appends any new given signal 
    #     to the signal log.
    #     """
    #     if signal.type == "SIGNAL":
    #         trade_entry = pd.Series(
    #             [
    #                 timestamp, signal.symbol
    #                 , signal.signal_type, price
    #                 , mode
    #             ],
    #             index = [
    #                 'timestamp', 'symbol_id', 
    #                 'direction', 'price', 'mode'
    #             ]
    #         )

    #         self.signal_log = self.signal_log.append(
    #             trade_entry, ignore_index = True
    #         )
    
    # def create_signal_log_csv(self):
    #     """
    #     Saves the trade log as a csv"""
    #     self.signal_log.to_csv("output/signal_log.csv")    

    def calculate_signals(self, event):
        """
        Generates a new set of signals based on the MAC
        SMA with the short window crossing the long window
        meaning a long entry and vice versa for a short entry.    

        Parameters
        event - A MarketEvent object. 
        """
        strategy_id = 99 # Buy and Hold S&P
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bar_date = self.bars.get_datetime()
                last_price = self.bars.get_latest_bar_value(
                        s, 'close_price'
                    )
                # Make a dataframe to add other indicators if needed
                
                if last_price > 0:                    
                    
                    symbol = s 
                    timestamp = dt.datetime.utcnow()
                    sig_dir = ""

                    # Buy/sell logic below 
                    if self.bought[s] == "OUT":
                        print("LONG signal generated on %s at price %s" %(
                            bar_date, last_price)
                        )
                        sig_dir = "LONG"
                        signal = SignalEvent(strategy_id, symbol, timestamp
                            ,sig_dir, 1.0
                        )
                        self.events.put(signal)
                        self.bought[s] = "LONG"
                        # self.update_signal_log(
                        #     signal, bar_date, last_price, 'ENTRY'
                        # )
                        self.bar_since_buy += 1
                    
                    elif self.bought[s] == 'LONG':
                        self.bar_since_buy += 1 
                        if self.bar_since_buy == 100:
                            print("EXIT signal generated on %s at price %s" %(
                                bar_date, last_price)
                            )
                            sig_dir = "EXIT"
                            signal = SignalEvent(strategy_id, symbol, timestamp
                                ,sig_dir, 1.0
                            )
                            self.events.put(signal)
                            self.bought[s] = "OUT"
                            # self.update_signal_log(
                            #     signal, bar_date, last_price, 'ENTRY'
                            # )
                            self.bar_since_buy = 0




if __name__ == "__main__":
    start_time = time.time()
    symbol_list = [8098]
    initial_capital = 10000.0
    heartbeat = 0.0
    start_date = dt.datetime(2015, 1, 1, 0, 0, 0)
    end_date = dt.datetime(2015, 6, 1, 0, 0, 0)

    backtest = TradingSession(
        symbol_list= symbol_list
        , initial_capital= initial_capital
        , heartbeat=0.0
        , session_start_dt= start_date
        , session_end_dt= end_date
        , session_type= 'backtest'
        , price_handler= SecDbPriceHandler
        , execution_handler= BetterSimulatedExecutionHandler
        , portfolio= Portfolio
        , strategy= Buy_And_Hold_Dummie
        , book= Book
        , money_management= MoneyManagement
        , risk_manager= None
        , performance= TradingStats
        , output_path=os.path.dirname(os.path.abspath(__file__))
    )

    backtest.start_trading()
    print(time.time()-start_time)
