#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# 
# xtb_session.py
# Author: Darren Yeap
import os 
import datetime as dt
import pprint
try:
    import Queue as queue
except ImportError:
    import queue
import time

class XtbSession:
    """Encapsules a trading session through XTB brokerage. Runs as an 
    event-driven engine.
    """
    def __init__(self, symbol_list, heartbeat, price_handler, execution_handler 
            , portfolio, strategy, connection, other_parameters={}):
        self.symbol_list = symbol_list
        self.heartbeat = heartbeat
        self.events = queue.Queue()

        self.connection = connection
        self.price_handler = price_handler
        self.execution_handler = execution_handler
        self.portfolio = portfolio
        self.strategy = strategy
        self.other_parameters = other_parameters

        self.signals = 0
        self.orders = 0

        self._generate_trading_instances()
        self._run_session()

    def _construct_price_handler(self):
        """Constructs price handler object. 

        Returns:
            [obj]: price handler object
        """
        price_handler_param = self.other_parameters.get('price_handler_param')
        if price_handler_param != None:
            return self.price_handler(
                events = self.events
                , symbol_list = self.symbol_list
                , connection = self.connection
                , barsize = price_handler_param['barsize']
            )

    def _construct_strategy(self):
        """
        Constructs strategy object. Must have price handler and events
        object already created. 

        Returns:
            [obj]: strategy object
        """
        if self.other_parameters.get('strategy_param') == None:
            return self.strategy(self.price_handler, self.events) 
        else:
            return self.strategy(
                self.price_handler, self.events, self.connection
                , **self.other_parameters.get('strategy_param')
            )

    def _construct_book(self):
        """
        Construct book object. Must have both price handler and connection
        object already created before calling this function. 

        Returns:
            [obj]: book object
        """
        return self.book(events=self.events, bars=self.price_handler
            , connection=self.connection)

    def _construct_money_management(self):
        """
        Construct money management object. Must have book object already created.

        Returns:
            [obj]: money management object
        """
        return self.money_management(bars=self.price_handler, book=self.book)

    def _construct_portfolio(self):
        """
        Construct portfolio object. Must have price handler object, book 
        object, money management object already created. 

        Returns:
            [obj]: portfolio object
        """
        return self.portfolio(
            bars = self.price_handler, events = self.events
            , connection = self.connection
        )

    def _construct_execution_handler(self):
        """
        Construct execution handler object. Must have events and connection
        object already created. 

        Returns:
            [type]: [description]
        """
        return self.execution_handler(
            events=self.events, connection = self.connection
        )

    def _generate_trading_instances(self):
        """
        Create each trading component classes. Starts with creating
        price handler then pass price handler to creating strategy,
        portfolio, and execution handler class. 
        """
        self.price_handler = self._construct_price_handler()
        self.strategy = self._construct_strategy()
        # self.book = self._construct_book()
        # self.money_management = self._construct_money_management()
        self.portfolio = self._construct_portfolio()
        self.execution_handler = self._construct_execution_handler()

    def _run_session(self):
        """
        Run a infinite loop trading session. If no event is found, 
        the model sleeps for the duration specified by heartbeat.
        """
        i = 0
        while True:
            try:
                print('Waking') 
                self.execution_handler.execute_pending_orders()
                self.price_handler.update_bars()
            except:
                pass
            else:
                while True:
                    try:
                        event = self.events.get(False)
                    except queue.Empty:
                        break
                    else:
                        if event is not None:
                            if event.type == 'MARKET':
                                self.strategy.calculate_signals(event)
                                self.portfolio.update_timeindex(event)
                            elif event.type == 'SIGNAL':
                                self.signals += 1  
                                self.portfolio.update_signal(event)
                            elif event.type == 'ORDER':
                                self.orders += 1
                                self.execution_handler.execute_order(event)
            print('Sleeping')
            time.sleep(self.heartbeat)

    def start_trading(self):
        """
        Starts the live or backtest algo and outputs strategy performance.
        """
        self._run_session()

