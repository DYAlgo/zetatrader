#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# performance.py
# Darren Jun Yi Yeap V0.1

import os
import os.path
import pandas as pd
import pkg_resources
import seaborn as sns
import matplotlib.pyplot as plt
from os import listdir
from os.path import isdir, join
from scipy.stats import kurtosis, skew

class TradingStats:
    """The performance class is a stats tracker for a trading session that
    can be used by different objects in a trading session to record 
    specific trading stats and output performance. 

    The key stats to track are: position vector, equity curve,
    signal log, fill log. 
    """
    def __init__(self, output_path = None, tearsheet=True, benchmark='SPY'):
        """Initialize the class.


        Keyword Arguments:
            output_path {str} -- Path to save performance outputs 
                (default: {'None'})
            benchmark {str} -- Benchmark to compare to. Defaults to 'SPY'
        """
        self.output_path = output_path
        self.equity_curve = pd.DataFrame()
        self.benchmark = benchmark
        self.tearsheet = tearsheet
        self.signal_log = self.construct_signal_log()
        self.trade_log = self.construct_trade_log()
        
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
            {'timestamp':[], 'strategy_id':[], 'symbol':[], 
            'direction':[], 'strength':[],'money_mang_type':[]}
        )

        signal_log = signal_log[['timestamp', 'strategy_id', 'symbol',
            'direction', 'strength','money_mang_type']]

        return signal_log

    def construct_trade_log(self):
        """
        This constructs a trade log for trade by trade record keeping
        and trade validation purpose
        """
        trade_log = pd.DataFrame(
            {'timestamp':[], 'symbol_id':[], 'quantity':[], 
            'direction':[], 'price':[],'commission':[]}
        )

        trade_log = trade_log[['timestamp', 'symbol_id', 'quantity',
            'direction', 'price','commission']]

        return trade_log

    def create_output_folders(self):
        """Check if the given path has the needed output folders. It it is not 
        found, create one. 
        """
        # Test if output file works
        if (self.output_path is None):
            # Call func to make current script dir output dir
            self.sciptpath_as_output_path()
        elif not os.path.exists(self.output_path):
            # Call func to make current script dir output dir
            self.sciptpath_as_output_path()
            
        folders_needed = ['equity', 'tradelog']

        if self.output_path is not None:
            # Loop each folder needed
            for folders in folders_needed:
                path_needed = os.path.join(self.output_path, folders)
                # If folder not found then make one
                if not os.path.exists(path_needed):
                    os.mkdir(path_needed)

    def sciptpath_as_output_path(self):
        """Replaces output path with current script path.
        """
        script_path = os.path.dirname(os.path.abspath(__file__))
        self.output_path = script_path
        print("None output file given.\nOutput file set as %s"%script_path)

    # ========================= #
    # BOOKEEPING FUNCTIONS
    # ========================= #
    def update_trade_log(self, fill):
        """Takes an fill event and adds the order into our trade log for 
        record keeping.
        
        Arguments:
            fill {obj} -- Fill Event 
        """
        if fill.type == 'FILL':
            trade_entry = pd.Series(
                [
                    fill.timeindex, fill.symbol, fill.quantity,
                    fill.direction, fill.fill_cost, fill.commission
                ], 
                index = ['timestamp', 'symbol_id', 'quantity', 
                'direction', 'price', 'commission']
            )

            self.trade_log = self.trade_log.append(
                trade_entry, ignore_index = True
            )


    # ========================
    # POST-BACKTEST STATISTICS
    # ========================
    def create_equity_curve_dataframe(self, all_holdings):
        """Creates a pandas DataFrame from the all_holdings
        list of dictionaries.
        
        Arguments:
            all_holdings {list} -- list of daily holdings dictionary
        """
        curve = pd.DataFrame(all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0+curve['returns']).cumprod()
        curve['rolling 25N volatility'] = curve['returns'].rolling(2).std()
        try:
            # Try to find and append benchmark
            bmk = self.compute_benchmark_return(
                curve.index[0], curve.index[-1]
            )
            # attached benchmark and compute path
            curve = curve.merge(bmk, how='left', on='datetime')
            curve['benchmark'].iloc[0] = 0.0
            curve['benchmark'] = curve['benchmark'].fillna(0)
            curve['benchmark'] = (1.0 + curve['benchmark']).cumprod()
            curve['underwater'] = (
                curve['equity_curve']/curve['equity_curve'].expanding(2).max()
            ) - 1 
        except:
            # Print Warning of missing benchmark
            print(f'Benchmark {self.benchmark} not found!') 
        else:
            # Update curve
            self.equity_curve = curve     

    def compute_benchmark_return(self, start_dt, end_dt):
        # Computes return path for benchmark under same time period 
        benchmark_rtn = pd.read_csv(
            pkg_resources.resource_stream(__name__, 'SPY.csv')
            , index_col=0, parse_dates=True
        )
        benchmark_rtn = benchmark_rtn.loc[start_dt: end_dt]
        benchmark_rtn.rename_axis("datetime", inplace=True)
        benchmark_rtn.rename(columns={'return':'benchmark'}, inplace=True)
        # Compute cumm return
        
        return benchmark_rtn 
    
    # ========================
    # SAVE PERFORMANCE STATS
    # ========================
    def save_equity_curve(self, all_holdings):
        """Save the output of equity curve dataframe as csv.
        """
        self.create_equity_curve_dataframe(all_holdings)
        while True:
            if os.path.isfile(
                self.output_path + '/equity/%s.csv'%self.output_number
            ):
                self.output_number+=1
            else:
                self.equity_curve.to_csv(
                    self.output_path + r'/equity/%s.csv'%self.output_number
                )
                print("Curve %s saved at "%self.output_number + 
                    self.output_path + r'/equity/%s.csv'%self.output_number
                )
                break
        if self.tearsheet:
            # Plot the return v benchmark
            # df = pd.melt(
            #     self.equity_curve, value_vars=['equity_curve', 'benchmark']
            #     , ignore_index=False
            # )
            # sns.lineplot(data=df, x='datetime', y='value', hue='variable')
            self.plot_tearsheet()


    def save_trade_log(self):
        """Save the trade log dataframe as a csv
        """
        while True:
            if os.path.isfile(
                self.output_path + '/tradelog/%s.csv'%self.output_number
            ):
                self.output_number+=1
            else:
                self.trade_log.to_csv(
                    self.output_path + r'/tradelog/%s.csv'%self.output_number
                )
                print("TradeLog %s saved at "%self.output_number + 
                    self.output_path + r'/tradelog/%s.csv'%self.output_number
                )
                break
    
    # ========================
    # PLOT TEARSHEET
    # ========================
    def plot_tearsheet(self):
        """Plots a tearsheet of the trading performance.

        Args:
            returns ([type]): [description]
            trade ([type]): [description]
        """
        # Create figure 
        fig = plt.figure(constrained_layout=True, figsize=(15, 12))
        gs = fig.add_gridspec(7, 3)

        # Plot the return v benchmark
        ax1 = fig.add_subplot(gs[0:2, :])
        ax1.plot(self.equity_curve.index, self.equity_curve['equity_curve']
            , label='Equity Curve'
        )
        ax1.plot(self.equity_curve.index, self.equity_curve['benchmark']
            , label='Benchmark'
        )
        ax1.legend()

        # Plot underwater curve
        ax2 = fig.add_subplot(gs[2:4, :])
        ax2.fill_between(self.equity_curve.index, 0, self.equity_curve['underwater']
            , facecolor='red'
        )

        # Plot rolling return volatility
        ax3 = fig.add_subplot(gs[4:6, :])
        ax3.plot(self.equity_curve.index, 
            self.equity_curve['rolling 25N volatility']
        )

        # Plot performance metric table
        df = pd.DataFrame(
            {
                'Annual Return %': [self.cal_annualized_return(self.equity_curve)]
                , 'Sharpe Ratio': [self.cal_sharpe_ratio(self.equity_curve)]
                , 'Max Drawdown %': [self.cal_max_drawdown(self.equity_curve)]
                , 'Gain to Pain': [self.cal_gain_to_pain(self.equity_curve)]
                , 'Skew': [self.cal_return_skew(self.equity_curve)]
                , 'Kurtosis': [self.cal_return_kurtosis(self.equity_curve)]
                , 'Sortino': [self.cal_sortino_ratio(self.equity_curve)]
            }
        )

        cell_text = []
        for row in range(len(df)):
            cell_text.append(df.iloc[row])
        ax4 = fig.add_subplot(gs[-1:, :])
        ax4.table(cellText=cell_text, colLabels=list(df.columns), loc='center')
        ax4.axis('off')
        plt.show()

    # ========================
    # METRIC CALCULATORS
    # ========================
    def cal_annualized_return(self, curve):
        """Computes the annualize return.

        Args:
            curve ([type]): equity curve
        """
        return round(((curve['equity_curve'].iloc[-1] - 1) / 
            (curve['equity_curve'].index[-1] 
            - curve['equity_curve'].index[0]).days
        ) * 365 * 100, 4)
    
    def cal_sharpe_ratio(self, curve):
        return round(((curve['returns']).mean()
            /(curve['returns']).std()), 4)

    def cal_max_drawdown(self, curve):
        return round(100*min(curve['underwater'].dropna()), 4)

    def cal_gain_to_pain(self, curve):
        curve = curve.dropna()
        return round(
            (curve['equity_curve'].iloc[-1]-1)/(-min(curve['underwater']))
            , 4)

    def cal_return_skew(self, curve):
        return round(skew(curve['returns'].dropna()), 3)

    def cal_return_kurtosis(self, curve):
        return round(kurtosis(curve['returns'].dropna()), 3)

    def cal_sortino_ratio(self, curve):
        return round(curve['returns'].mean()/
            curve[curve['returns']<0]['returns'].std(), 4) 