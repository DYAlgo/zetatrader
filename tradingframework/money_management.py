#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# money_management.py
# Darren Jun Yi Yeap 03/07/2020
import math
from tradingframework.event import OrderEvent


class MoneyManagement:
    """A class object that takes in Signal Event and resizes  
    a trade with a given money management method in the context of 
    a portfolio.  
    """
    def __init__(self, book, lotsize=1):
        """Initialize the object.
        
        Arguments:
            book {obj} -- Book object. 
        """
        self.book=book
        self.lotsize=lotsize
        self.bars=self.book.bars
        self.money_management_dict = {
            0: self.generate_naive_order
            , 1: self.generate_naive_order_stackable
            , 2: self.generate_dollar_amount_order
            , 3: self.generate_dollar_amount_order_stackable
        }
        

    # ========================================= #
    # Money Management algo
    # ========================================= #
    def resized_order(self, event):
        """Returns a Order Event generated from a money management
        method that specified through the money management dictionary
        
        Arguments:
            event {obj} -- Signal Event object
        """
        identifier = event.money_management_key
        try:
            order_event = self.money_management_dict[identifier](event)
            return order_event
        except KeyError as e:
            print("%s \n"%e +
                "The money management method specified in Signal Event "+
                "was not found.")
            raise
        

    # ========================================= #
    # money management types
    # ========================================= #
    def generate_naive_order(self, signal):
        """Returns an order event to buy/sell the given the number 
        of units represented by the signal strength rounded down to
        nearest lot size. A signal to buy 101 shares where a lot is 
        100 shares will produce a buy order for 100 shares or 1 lot. 
        """
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        mkt_quantity = math.floor(signal.strength/self.lotsize)*self.lotsize
        cur_quantity = self.book.current_positions[symbol]
        order_type = 'MKT'

        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')   
    
        if direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        if direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
        return order        
    
    def generate_naive_order_stackable(self, signal):
        """Returns an order event to buy/sell the given number of units 
        represented by the signal strength rounded down to the nearest lot 
        size. This is not limited to only one position. So if we are already 
        long symbol x, we will still go long again if we recieve another 
        signal to buy symbol x. 
        """
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        mkt_quantity = math.floor(signal.strength/self.lotsize)*self.lotsize
        cur_quantity = self.book.current_positions[symbol]
        order_type = 'MKT'

        if direction == 'LONG':
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT':
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')   
    
        if direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        if direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
        return order

    def generate_dollar_amount_order(self, signal):
        """Generates a order that buys an equivalent of a fixed amount 
        determined by the strength of the signal. Strength of 1 = 1 dollar. It
        will not return an order if we already have a position for the given 
        symbol.
        
        Arguments:
            signal {[obj]} -- Signal event
        """
        order = None
        

        symbol = signal.symbol
        last_price = self.bars.get_latest_bar_value(symbol, "close_price")
        direction = signal.signal_type
        investment_amt = signal.strength
        mkt_quantity = investment_amt//last_price
        mkt_quantity=math.floor(mkt_quantity/self.lotsize)*self.lotsize

        cur_quantity = self.book.current_positions[symbol]
        order_type = 'MKT'
        
        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')  
        return order

    def generate_dollar_amount_order_stackable(self, signal):
        """Generates a order that buys an equivalent of a fixed amount 
        determined by the strength of the signal. Strength of 1 = 1 dollar.
        If a position is already establish for given symbol, we will still
        make return an order event for it. 
        
        Arguments:
            signal {[type]} -- Signal event
        """
        order = None
        

        symbol = signal.symbol
        last_price = self.bars.get_latest_bar_value(symbol, "close_price")
        direction = signal.signal_type
        investment_amt = signal.strength
        mkt_quantity = investment_amt//last_price
        mkt_quantity=math.floor(mkt_quantity/self.lotsize)*self.lotsize

        order_type = 'MKT'
        
        if direction == 'LONG':
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT':
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')  
        return order