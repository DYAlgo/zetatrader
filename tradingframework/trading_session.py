#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# trading_session.py
# Darren Jun Yi Yeap V0.1

import os 
import datetime as dt
import pprint
try:
    import Queue as queue
except ImportError:
    import queue
import time

class TradingSession(object):
    """
    Enscapsulates the settings and components for carrying out
    a pure event-driven backtest and trading.
    """

    def __init__(
        self, symbol_list, initial_capital=0.0, heartbeat=0.0
        , session_start_dt=None, session_end_dt=None, session_type='backtest' 
        , lotsize=None, price_handler=None, execution_handler=None, portfolio=None
        , strategy=None, book=None, money_management=None, risk_manager=None
        , performance=None, output_path=None, strategy_parameters=None
    ):
        """Initialize the class object.
        
        Arguments:
            symbol_list {list} -- A list of symbol identifier 
        
        Keyword Arguments:
            initial_capital {float} -- Starting capital for backtest session 
                (default: {0.0})
            heartbeat {float} -- Sleep time between each session loop 
                (default: {0.0})
            session_start_dt {datetime} -- Starting datetime of backtest 
                (default: {None})
            session_end_dt {datetime} -- Ending datetime of backtest 
                (default: {None})
            session_type {str} --  Use 'backtest' or 'live' to control session 
                type (default: {'backtest'})
            lotsize {int} -- The standadize number of incremental units tradable   
                (default: {None})
            price_handler {class} -- data handler object (default: {None})
            execution_handler {class} -- executionhandler object 
                (default: {None})
            portfolio {class} -- portfolio object (default: {None})
            strategy {class} -- strategy object (default: {None})
            money_management {class} -- money management object 
                (default: {None})
            risk_manager {class} -- risk manager object (default: {None})
            performance {class} -- performance object (default: {None})
            output_path {str} -- The path to save all outputs (i.e: equity curve)
            strategy_parameters {dict} -- Dict of parameter variables to parse into 
                strategy class. Keys in dict are parameter names. 
        """ 
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.session_start_dt = session_start_dt
        self.session_end_dt = session_end_dt
        self.session_type = session_type
        self.events = queue.Queue()

        self.price_handler = price_handler
        self.execution_handler = execution_handler
        self.portfolio = portfolio
        self.strategy = strategy
        self.book = book
        self.money_management = money_management
        self.risk_manager = risk_manager
        self.performance = performance
        self.output_path = output_path
        self.strategy_parameters = strategy_parameters

        self.signals = 0
        self.orders = 0
        self.fills = 0
        
        self._generate_trading_instances()

    def _generate_trading_instances(self):
        """
        Generates the trading instance objects from 
        their class types. It must follow the sequence 
        starting from initializing price handler to execution handler
        """
        # Initialize price_handler class
        if self.session_type == 'backtest':
            # Add log here
            self.price_handler = self.price_handler(
                self.events, self.symbol_list
            )
            self.price_handler.set_handler_datetime(
                self.session_start_dt-dt.timedelta(days = 1)
                , self.session_end_dt
            )
        elif self.session_type =='live':
            pass
        else:
            print('Unknown session type detected.'
                + 'No price handler initialize.'
            )
            
        # Initialize strategy class based on whether is is parameterless or not
        if self.strategy_parameters==None:
            self.strategy = self.strategy(self.price_handler, self.events) 
        else:
            try:
                if type(self.strategy_parameters)==dict:
                    self.strategy = self.strategy(
                        self.price_handler, self.events, **self.strategy_parameters
                    )
            except:
                raise ValueError("Incorrect strategy parameter variable given.")
        
        # Initialize Performance Class
        self.performance = self.performance(self.output_path)

        # Initialize Portfolio Class
        self.portfolio = self.portfolio(
            self.initial_capital, self.price_handler, self.events
            , self.session_type, self.book, self.money_management
            , self.risk_manager, self.performance
        )

        # Initialize execution handler_class
        if self.session_type == 'backtest':
            # Simulated Execution Handler requires price handler
            self.execution_handler = self.execution_handler(
                self.events, self.price_handler
            )
        elif self.session_type == 'live':
            pass
        else:
            print('Unknown session type detected.'
                + 'No execution handler initialize.'
            )

        # Initialize performance (Maybe move this into portfolio)

        print(
            "Initializing objects...\n"
            , "Data Handler: %s \n" %self.price_handler
            , "Strategy %s \n" %self.strategy
            , "Portfolio %s \n" %self.portfolio
            , "Execution Handler %s \n" %self.execution_handler
        )
       
    def _continue_session_loop(self):
        """Determines when to end trading session loop
        """
        if self.session_type == 'backtest':
            return self.price_handler.continue_backtest
        else:
            return dt.datetime.now() < self.session_end_dt

    def _run_session(self):
        """
        Executes the backtest.
        """
        i = 0
        while True:
            if self._continue_session_loop() is True:
                i += 1
                print(i)
                # Checks for price event
                self.price_handler.update_bars()  
            else:
                break

            # Event driven logic 
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            # Calculate signal & update portfolio value
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                        elif event.type == 'SIGNAL':
                            # Turns signal into order event adjusted for risk
                            self.signals += 1  
                            self.portfolio.update_signal(event)
                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                        elif event.type == 'FILL':
                            # Update portolio value and position 
                            self.fills += 1
                            self.portfolio.update_fill(event)
            time.sleep(self.heartbeat)

    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """
        self.portfolio.save_portfolio_performance()

    def start_trading(self):
        """
        Starts the live or backtest algo and outputs strategy performance.
        """
        self._run_session()
        self._output_performance()