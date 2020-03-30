#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# money_management.py
# Darren Jun Yi Yeap 03/07/2020
from tradingframework.event import OrderEvent


class MoneyManagement:
    """A class object that takes in Signal Event and resizes  
    a trade with a given money management method in the context of 
    a portfolio.  
    """
    def __init__(self, book):
        """Initialize the object.
        
        Arguments:
            book {obj} -- Book object. 
        """
        self.book = book
        self.money_management_dict = {
            0: self.generate_naive_order
        }
        

    # ========================================= #
    # Money Management algo
    # ========================================= #
    def resized_order(self, event):
        """Returns a Order Event generated from a money management
        method that specified through the 
        
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
        """Returns an order event to buy/sell the given the rounded 
        number of units represented by the signal strength.
        """
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        mkt_quantity = signal.strength
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

    