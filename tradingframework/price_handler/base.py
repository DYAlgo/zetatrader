#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# AbstractPriceHandler.py
# Darren Jun Yi Yeap V0.1
import pymysql 
import numpy as np 
import pandas as pd 
import datetime as dt 

from abc import ABCMeta, abstractmethod
from tradingframework.event import MarketEvent, CloseEvent

class AbstractPriceHandler:
    """
    Abstract base class providing an interface for all subsequent (inherited)
    price handler (both live and historical). The objective of the datahandler 
    is to output price bar for each symbol requested. At the minimum, the 
    Open, High, Low, Close, Volume/Open Interest is returned in each bar.

    This is meant to replicate how a live trading strategy works as market
    price flows down the event-driven system. 
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bar(self, symbol):
        """
        Returns the last bar updated.
        """
        raise NotImplementedError("Should implement get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars updated.
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the last bar.
        """
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        """
        Returns one of the Open, High, Low, Close, Volume or OI
        from the last bar.
        """
        raise NotImplementedError("Should implement get_latest_bar_value()")

    @abstractmethod
    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Returns the last N bar values from the
        latest_symbol list, or N-k if less available.
        """
        raise NotImplementedError("Should implement get_latest_bars_values()")

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bars to the bars_queue for each symbol
        in a tuple OHLCVI format: (datetime, open, high, low,
        close, volume, open interest).
        """
        raise NotImplementedError("Should implement update_bars()")


# class Abstract_Tick_Handler:
#     """
#     A slightly modified version of Abstract Price Handler that will mimick a 
#     price handler used in tick-by-tick trading where only the last 
#     price (tick) flows through the event-driven system.  
#     """

#      __metaclass__ = ABCMeta

     