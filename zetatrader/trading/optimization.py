#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import itertools
import pandas as pd

# Import own modules
from zetatrader.trading.backtest import TradingSession


class Optimization:
    """Carries out parameter optimization for a trading strategy."""

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
        strategy_parameters_dict=None,
    ):
        self.symbol_dict = symbol_dict
        self.initial_capital = initial_capital
        self.session_start_dt = session_start_dt
        self.session_end_dt = session_end_dt

        self.price_handler = price_handler
        self.execution_handler = execution_handler
        self.portfolio = portfolio
        self.strategy = strategy
        self.performance = performance
        self.output_path = output_path
        self.backtest_parameters = backtest_parameters
        self.strategy_parameters_dict = strategy_parameters_dict

    def _construct_parameter_combination(self):
        # Create list of possible strategt parameter combinations
        param_names = list(self.strategy_parameters_dict.keys())
        param_combinations = []
        for comb in itertools.product(
            *(self.strategy_parameters_dict[p] for p in param_names)
        ):
            params = {param_names[k]: comb[k] for k in range(len(param_names))}
            param_combinations.append(params)
        return param_combinations

    def _run_backtest_instance(self, strat_param):
        # Run a single backtest for the given strategy parameters
        backtest = TradingSession(
            symbol_dict=self.symbol_dict,
            initial_capital=self.initial_capital,
            session_start_dt=self.session_start_dt,
            session_end_dt=self.session_end_dt,
            price_handler=self.price_handler,
            execution_handler=self.execution_handler,
            portfolio=self.portfolio,
            strategy=self.strategy,
            performance=self.performance,
            output_path=self.output_path,
            backtest_parameters=self.backtest_parameters,
            strategy_parameters=strat_param,
            verbose=False,
            save_results=False
        )

        return backtest.start_trading()

    def optimize_strategy(self):
        optimization_performance = []
        param_combinations = self._construct_parameter_combination()

        for sp in param_combinations:
            print(f"Backtesting with parameters: {sp}")
            _, _, portfolio_metrics, _ = self._run_backtest_instance(sp)
            optimization_performance.append({**sp, **portfolio_metrics})
        return pd.DataFrame(optimization_performance)
