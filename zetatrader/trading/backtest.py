#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import pandas as pd
import datetime as dt

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
        self,
        symbol_dict,
        initial_capital=0.0,
        session_start_dt=None,
        session_end_dt=None,
        price_handler=None,
        execution_handler=None,
        portfolio=None,
        strategy=None,
        performance=None,
        output_path=None,
        backtest_parameters={},
        strategy_parameters={},
    ):
        """Initialize the class object.

        Arguments:
            symbol_list {list} -- A list of symbol identifier

        Keyword Arguments:
            initial_capital {float} -- Starting capital for backtest session
                (default: {0.0})
            session_start_dt {datetime} -- Starting datetime of backtest
                (default: {None})
            session_end_dt {datetime} -- Ending datetime of backtest
                (default: {None})
            lotsize {int} -- The standadize number of incremental units tradable
                (default: {None})
            price_handler {class} -- data handler object (default: {None})
            execution_handler {class} -- executionhandler object
                (default: {None})
            portfolio {class} -- portfolio object (default: {None})
            strategy {class} -- strategy object (default: {None})
            performance {class} -- performance object (default: {None})
            output_path {str} -- The path to save all outputs (i.e: equity curve)
            strategy_parameters {dict} -- Dict of parameter variables to parse
                into each class. Keys in dict are class names. Sub-keys are
                parameter names
        """
        self.symbol_dict = symbol_dict
        self.initial_capital = initial_capital
        self.session_start_dt = session_start_dt
        self.session_end_dt = session_end_dt
        self.events = queue.Queue()

        self.price_handler = price_handler
        self.execution_handler = execution_handler
        self.portfolio = portfolio
        self.strategy = strategy
        self.performance = performance
        self.output_path = output_path
        self.backtest_parameters = backtest_parameters
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
        if self.backtest_parameters.get("price_handler_param") == None:
            # TODO: Add logging here
            self.price_handler = self.price_handler(
                events=self.events,
                symbol_dict=self.symbol_dict,
                start_dt=self.session_start_dt,
                end_dt=self.session_end_dt,
            )
        else:
            # TODO: Add logging here
            self.price_handler = self.price_handler(
                events=self.events,
                symbol_dict=self.symbol_dict,
                start_dt=self.session_start_dt,
                end_dt=self.session_end_dt,
                **self.backtest_parameters.get("price_handler_param")
            )

        # INITIALIZE STRATEGY CLASS
        self.strategy = self.strategy(
            self.price_handler, self.events, **self.strategy_parameters
        )

        # INIT PERFORMANCE CLASS
        if self.backtest_parameters.get("performance_param") == None:
            self.performance = self.performance(self.output_path)
        else:
            self.performance = self.performance(
                self.output_path, **self.backtest_parameters.get("performance_param")
            )

        # INITIALIZE PORTFOLIO CLASS
        self.portfolio = self.portfolio(
            initial_capital=self.initial_capital,
            bars=self.price_handler,
            events=self.events,
            performance=self.performance,
            **self.backtest_parameters.get("portfolio", {})
        )

        # INIT EXECUTION HANDLER CLASS
        self.execution_handler = self.execution_handler(
            self.events,
            self.price_handler,
            **self.backtest_parameters.get("execution_param", {})
        )

        print(
            "Initializing objects...\n",
            "Data Handler: %s \n" % self.price_handler,
            "Strategy %s \n" % self.strategy,
            "Portfolio %s \n" % self.portfolio,
            "Execution Handler %s \n" % self.execution_handler,
        )

    def _continue_session_loop(self):
        """Determines when to end trading session loop"""
        return self.price_handler.continue_backtest

    def _run_session(self):
        """
        Executes the backtest.
        """
        i = 0
        while True:
            if self._continue_session_loop() is True:
                i += 1
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
                        if event.type == "MARKET":
                            # Calculate signal & update portfolio value
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                        elif event.type == "SIGNAL":
                            # Turns signal into order event adjusted for risk
                            self.signals += 1
                            self.portfolio.update_signal(event)
                        elif event.type == "ORDER":
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                        elif event.type == "FILL":
                            # Update portolio value and position
                            self.fills += 1
                            self.portfolio.update_fill(event)

    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """
        # Analyze and Store Equity Curve
        equity_curve = self.portfolio.get_equity_curve()
        (
            equity_curve,
            portfolio_metrics,
        ) = self.performance.calculate_portfolio_performance(equity_curve)
        print(pd.Series(portfolio_metrics))

        # Analyze and Store trade data
        trade_data = self.performance.save_trade_log()

        return (equity_curve, trade_data, portfolio_metrics)

    def start_trading(self):
        """
        Starts the live or backtest algo and outputs strategy performance.
        """
        self._run_session()
        return self._output_performance()
