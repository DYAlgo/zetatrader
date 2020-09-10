#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# portfolio.py
# Darren Jun Yi Yeap V0.1

import pandas as pd
import datetime as dt

class Portfolio:
    """The Portfolio class handles portfolio position, value
    , performance tracking, and manages interaction of 
    signal event, order event, fill event between book
    , money_management, risk_management, and performance.
    
    It uses Book class to track value of all instruments at a resolution
    of a "bar" or tick, i.e. secondly, minutely, 5-min, 30-min
    , 60 min or EOD and ticks. 
    """
    def __init__(self, initial_capital, bars, events, session_type='backtest'
        ,lotsize=None, book = None, money_management=None, risk_manager=None
        , performance=None, 
    ):
        """Initializes portfolio class
        
        Arguments:
            bars {[type]} -- [description]
            events {[type]} -- [description]
        
        Keyword Arguments:
            session_type {str} -- [description] (default: {'backtest'})
            book {[type]} -- [description] (default: {None})
            money_management {[type]} -- [description] (default: {None})
            risk_manager {[type]} -- [description] (default: {None})
            performance {[type]} -- [description] (default: {None})
        """
        self.initial_capital = initial_capital
        self.bars = bars
        self.events = events
        self.session_type = session_type
        self.lotsize=lotsize

        self.book = book
        self.money_management = money_management
        self.risk_manager = risk_manager
        self.performance = performance
    
        self.construct_portfolio()

    def __str__(self):
        return "Default Portfolio Class"

    def construct_portfolio(self):
        """Initialize the 4 key components of a portfolio - the book
        , the money_management object, the risk manager, and the performance
        tracker (In that order).
        """
        # Create book
        if self.book is not None:
            self.book = self.book(self.initial_capital, self.bars
                , self.session_type
            )
            
        # Create money_management
        if self.money_management is not None:
            if type(self.lotsize)==int:
                self.money_management = self.money_management(self.book, self.lotsize)
            else:
                self.money_management = self.money_management(self.book)  

        # Create risk_manager
        if self.risk_manager is not None:
            self.risk_manager = self.risk_manager()


    # ========================= # 
    # Update Portfolio Index,
    # Value, and Position  
    # ========================= #  
    def update_timeindex(self, event):
        """Updates portfolio value through book object"""
        self.book.update_timeindex(event)

    
    # ========================= #
    # SIGNAL HANDLING 
    # ========================= #
    def update_signal(self, event):
        """Acts on the SignalEvent and utilize money_management
        and risk management 
        
        Arguments:
            event {obj} -- SignalEvent object 
        """
        if event.type == 'SIGNAL':
            order_event = self.money_management.resized_order(event)
            # Can also parse it thru a risk manager here.
            self.events.put(order_event)
    

    # ======================
    # FILL/POSITION HANDLING
    # ======================
    def update_fill(self, event):
        """
        Takes a Fill Event to update our portfolio position and holdings
        plus recording this filled in our performance. 
        
        Arguments:
            event {obj} -- Fill Event
        """
        if event.type == 'FILL':
            self.book.update_positions_from_fill(event)
            self.book.update_holdings_from_fill(event)
            self.performance.update_trade_log(event)


    # ======================
    # SAVE PORTFOLIO
    # PERFORMANCE
    # ======================
    def save_portfolio_performance(self):
        """Save all portfolio level performance statistics through 
        performance object. These are:
        1. equity curve record 
        2. trade log. 
        """
        self.performance.save_equity_curve(self.book.all_holdings)
        self.performance.save_trade_log()