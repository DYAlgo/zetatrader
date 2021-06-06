#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# trading_stats.py
# Darren Yeap

import os
import os.path
import numpy as np
import pandas as pd
import pkg_resources
import seaborn as sns
import matplotlib.pyplot as plt
from os import listdir, times
from os.path import isdir, join
from scipy.stats import kurtosis, skew


class TradingStats:
    """The performance class is a stats tracker for a trading session that
    can be used by different objects in a trading session to record
    specific trading stats and output performance.

    The key stats to track are: position vector, equity curve,
    signal log, fill log.
    """

    def __init__(self, output_path=None, tearsheet=True, benchmark="SPY"):
        """Initialize the class.


        Keyword Arguments:
            output_path {str} -- Path to save performance outputs
                (default: {'None'})
            benchmark {str} -- Benchmark to compare to. Defaults to 'SPY'
        """
        self.output_path = output_path
        self.benchmark = benchmark
        self.tearsheet = tearsheet
        self.signal_log = self.construct_signal_log()

        self.create_output_folders()
        self.output_number = 1

    # ========================= #
    # CONSTRUCT CLASS
    # ========================= #
    def construct_signal_log(self):
        """
        Return a DataFrame where
        """
        signal_log = pd.DataFrame(
            {
                "timestamp": [],
                "strategy_id": [],
                "symbol": [],
                "direction": [],
                "strength": [],
                "money_mang_type": [],
            }
        )

        signal_log = signal_log[
            [
                "timestamp",
                "strategy_id",
                "symbol",
                "direction",
                "strength",
                "money_mang_type",
            ]
        ]

        return signal_log

    def create_output_folders(self):
        """Check if the given path has the needed output folders. It it is not
        found, create one.
        """
        # Test if output file works
        if self.output_path is None:
            # Call func to make current script dir output dir
            self.sciptpath_as_output_path()
        elif not os.path.exists(self.output_path):
            # Call func to make current script dir output dir
            self.sciptpath_as_output_path()

        folders_needed = ["equity", "tradelog"]

        if self.output_path is not None:
            # Loop each folder needed
            for folders in folders_needed:
                path_needed = os.path.join(self.output_path, folders)
                # If folder not found then make one
                if not os.path.exists(path_needed):
                    os.mkdir(path_needed)

    def sciptpath_as_output_path(self):
        """Replaces output path with current script path."""
        script_path = os.path.dirname(os.path.abspath(__file__))
        self.output_path = script_path
        print("None output file given.\nOutput file set as %s" % script_path)

    # ========================
    # POST-BACKTEST STATISTICS
    # ========================
    def create_equity_curve_dataframe(self, holdings_data, timescale):
        """Creates a pandas DataFrame from the all_holdings
        list of dictionaries.

        Arguments:
            all_holdings {list} -- list of daily holdings dictionary
        """
        curve = pd.DataFrame(holdings_data)
        curve.set_index("datetime", inplace=True)
        curve["returns"] = curve["total"].pct_change()
        curve["equity_curve"] = (1.0 + curve["returns"]).cumprod()
        curve["rolling 25N volatility"] = curve["returns"].rolling(2).std()

        # Upsample to timescale
        curve = curve.resample(timescale).last().dropna()

        try:
            # Try to find and append benchmark
            bmk = self.compute_benchmark_return(curve.index[0], curve.index[-1])
            bmk = bmk.resample(timescale).last().dropna()
            # attached benchmark and compute path
            curve = curve.merge(bmk, how="left", on="datetime")
            curve["benchmark"].iloc[0] = 0.0
            curve["benchmark"] = curve["benchmark"].fillna(0)
            curve["benchmark"] = (1.0 + curve["benchmark"]).cumprod()
            curve["underwater"] = (
                curve["equity_curve"] / curve["equity_curve"].expanding(2).max()
            ) - 1
        except:
            # Print Warning of missing benchmark
            print(f"Benchmark {self.benchmark} not found!")
        else:
            # Update curve
            return curve

    def compute_benchmark_return(self, start_dt, end_dt):
        # Computes return path for benchmark under same time period
        benchmark_rtn = pd.read_csv(
            pkg_resources.resource_stream(__name__, "SPY.csv"),
            index_col=0,
            parse_dates=True,
        )
        benchmark_rtn = benchmark_rtn.loc[start_dt:end_dt]
        benchmark_rtn.rename_axis("datetime", inplace=True)
        benchmark_rtn.rename(columns={"return": "benchmark"}, inplace=True)
        # Compute cumm return

        return benchmark_rtn

    def calculate_trading_stats(self, equity_curve):
        """Returns a dictionary of consisting of annualized return,
        annualized volatility, sharpe ratio, sortino ratio, MAR ratio,
        Max Drawdown, length of maximum drawdown, % of positive days

        Args:
            equity_curve ([type]): [description]
            timescale ([type]): [description]
        """
        metrics = {}
        metrics["Annualized Return %"] = self.calculate_annual_return(
            equity_curve["returns"]
        )
        metrics["Annualized Volatility %"] = self.calculate_annual_volatility(
            equity_curve["returns"]
        )
        metrics["Max Drawdown"] = self.calculate_max_drawdown(
            equity_curve["underwater"]
        )
        metrics["Sharpe Ratio"] = self.calculate_sharpe_ratio(
            metrics["Annualized Return %"], metrics["Annualized Volatility %"]
        )
        metrics["Sortino Ratio"] = self.calculate_sortino_ratio(equity_curve["returns"])
        metrics["MAR"] = self.calculate_mar(
            metrics["Annualized Return %"], metrics["Max Drawdown"]
        )
        metrics["Return Skew"] = self.calculate_return_skew(equity_curve["returns"])
        metrics["Return Kurtosis"] = self.calculate_return_kurtosis(
            equity_curve["returns"]
        )

        return pd.Series(metrics)

    def calculate_portfolio_performance(self, holdings_data, timescale="1D"):
        """Compute both the equity curve data and portfolio performance metrices.

        Args:
            equity_curve ([type]): [description]

        Returns:
            [type]: [description]
        """
        holdings_data = self.create_equity_curve_dataframe(holdings_data, timescale)
        portfolio_metrics = self.calculate_trading_stats(holdings_data)

        # Save performance to csv file
        if self.tearsheet:
            self.plot_tearsheet(holdings_data)

        return (holdings_data, portfolio_metrics)

    # ========================
    # SAVE PERFORMANCE STATS
    # ========================
    def save_equity_curve(self, equity_curve):
        """Saves of equity curve dataframe as csv."""
        while True:
            if os.path.isfile(self.output_path + "/equity/%s.csv" % self.output_number):
                self.output_number += 1
            else:
                equity_curve.to_csv(
                    self.output_path + r"/equity/%s.csv" % self.output_number
                )
                print(
                    "Curve %s saved at " % self.output_number
                    + self.output_path
                    + r"/equity/%s.csv" % self.output_number
                )
                break

    def save_trade_log(self, trade_log):
        """Save the trade log dataframe as a csv"""
        while True:
            if os.path.isfile(
                self.output_path + "/tradelog/%s.csv" % self.output_number
            ):
                self.output_number += 1
            else:
                trade_log.to_csv(
                    self.output_path + r"/tradelog/%s.csv" % self.output_number
                )
                print(
                    "TradeLog %s saved at " % self.output_number
                    + self.output_path
                    + r"/tradelog/%s.csv" % self.output_number
                )
                break
        return trade_log

    # ========================
    # PLOT TEARSHEET
    # ========================
    def plot_tearsheet(self, equity_curve):
        """Plots a tearsheet of the trading performance.

        Args:
            returns ([type]): [description]
            trade ([type]): [description]
        """
        # Create figure
        fig = plt.figure(figsize=(15, 15))
        gs = fig.add_gridspec(7, 3)

        # Plot the return v benchmark
        ax1 = fig.add_subplot(gs[0:2, :])
        ax1.plot(
            equity_curve.index,
            equity_curve["equity_curve"],
            label="Equity Curve",
        )
        ax1.plot(equity_curve.index, equity_curve["benchmark"], label="Benchmark")
        ax1.legend()

        # Plot underwater curve
        ax2 = fig.add_subplot(gs[2:4, :], sharex=ax1)
        ax2.fill_between(
            equity_curve.index, 0, equity_curve["underwater"], facecolor="red"
        )
        ax2.set_title("Underwater Curve")

        # Plot rolling return volatility
        ax3 = fig.add_subplot(gs[4:6, :], sharex=ax1)
        ax3.plot(equity_curve.index, equity_curve["rolling 25N volatility"])
        ax3.set_title("rolling 25N volatility")

        plt.tight_layout()
        plt.show()

    # ========================
    # METRIC CALCULATORS
    # ========================
    def calculate_annual_return(self, daily_returns):
        # Assumes each bar represents a trading day
        return round(daily_returns.mean() * 252 * 100, 5)

    def calculate_annual_volatility(self, daily_returns):
        return round(daily_returns.std() * np.sqrt(252) * 100, 5)

    def calculate_sharpe_ratio(self, avg_return, avg_volatility):
        return round(avg_return / avg_volatility, 4)

    def calculate_max_drawdown(self, underwater_ts):
        return round(100 * abs(min(underwater_ts.dropna())), 4)

    def calculate_mar(self, total_return, max_drawdown):
        return round(total_return / max_drawdown)

    def calculate_gain_to_pain(self, equity_ts, underwater_ts):
        equity_ts = equity_ts.dropna()
        return round((equity_ts.iloc[-1] - 1) / (-min(underwater_ts)), 4)

    def calculate_return_skew(self, return_ts):
        return round(skew(return_ts.dropna()), 3)

    def calculate_return_kurtosis(self, return_ts):
        return round(kurtosis(return_ts.dropna()), 3)

    def calculate_sortino_ratio(self, return_ts):
        return round(return_ts.mean() / return_ts[return_ts < 0].std(), 4)
