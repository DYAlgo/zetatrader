#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# sec_db_price_handler.py
# Darren Jun Yi Yeap V0.1
import pymysql 
import numpy as np 
import pandas as pd 
import datetime as dt

from data_framework.credentials import sec_db_cred
from tradingframework.event import MarketEvent
from tradingframework.price_handler.base import AbstractPriceHandler


class SecDbPriceHandler(AbstractPriceHandler):
    """Sec_DB_Price_Handler is a price handler class that pulls the data from
    Sec_DB. The data is forward filled and returns data through a drip like 
    process. This is at least x2 faster then querying Sec_DB per bar. 
    """
    def __init__(self, events, symbol_list, sec_db_pw = sec_db_cred
        , insample_size_est = 2000
    ):
        """Initialize Sec_DB_Price_Handler object 
        
        Arguments:
            Abstract_Price_Handler {class} -- Abstract base class of price 
                handler
            events {class} -- MarketEvent class from event
            symbol_list {list} -- List containing symbol id for symbols to 
                trade 
        
        Keyword Arguments:
            sec_db_pw {[type]} -- [description] (default: {sec_db_cred})
            insample_size_est {int} -- [description] (default: {2000})
        """
        self.events = events
        self.sec_db_pw = sec_db_cred
        self.symbol_list = symbol_list
        self.insample_size_est = insample_size_est

        self.bar_index = -1
        self.continue_backtest = True
        self.sec_db_conn = pymysql.connect(
            host = self.sec_db_pw['db_host']
            , user = self.sec_db_pw['db_user']
            , passwd = self.sec_db_pw['db_pass']
            , db = self.sec_db_pw['db_name']
        )
        self.symbol_data = {} 
        self.latest_symbol_data = pd.DataFrame()


    def __str__(self):
        """Prints the name of this class
        """
        return "Sec_DB_Price_Handler"

    # ================================#
    # CONSTRUCTOR
    # ================================#    
    def construct_symbol_data(self):
        """
        Creates a dictionary of price data with respect to the symbol(keys)
        """
        # Create list holding all the data 
        comb_index = None
        data = {}
        max_len = 0
        most_data_symbol = 0
        outsample_size = None
        total_size = None

         #Load the data without pre insample data
        for i in self.symbol_list:
            # Get price data 
            query = """(SELECT price_date, open_price, high_price, low_price,
            close_price, adj_close_price, volume FROM 
            daily_price WHERE symbol_id = %s AND price_date BETWEEN '%s' 
            AND '%s' ) ORDER BY price_date ASC"""%(
                i, self.start_date+dt.timedelta(days=1), self.end_date
            )
            price_data = pd.read_sql_query(query, con = self.sec_db_conn)
            price_data.set_index("price_date", inplace=True)
            # Update length comparison and 
            if len(price_data) > max_len:
                max_len = len(price_data)
                most_data_symbol = i
            data[i] = price_data
        
        # Take the index of the largest data set and apply it as index to all 
        # Other dataframe
        if len(self.symbol_list)>1:
            comb_index = data[most_data_symbol].index
            # Set all data set with this index
            for i in self.symbol_list:
                data[i] = data[i].reindex(
                    index = comb_index, method="pad"
                )
                data[i].reset_index(inplace=True)
        else:
            data[self.symbol_list[0]].reset_index(inplace=True)

        outsample_size = len(data[self.symbol_list[0]])
        
        # Load the data furthur lookback set the index for first insample data
        for i in self.symbol_list:
            # Get price data 
            query = """(SELECT price_date, open_price, high_price, low_price,
            close_price, adj_close_price, volume FROM 
            daily_price WHERE symbol_id = %s AND price_date BETWEEN '%s' 
            AND '%s' ) ORDER BY price_date ASC"""%(
                i, self.start_date-dt.timedelta(days=self.insample_size_est)
                , self.end_date
            )
            price_data = pd.read_sql_query(query, con = self.sec_db_conn)
            price_data.set_index("price_date", inplace=True)
            # Update length comparison and 
            if len(price_data) > max_len:
                max_len = len(price_data)
                most_data_symbol = i
            data[i] = price_data
        
        # Take the index of the largest data set and apply it as index to all 
        # Other dataframe
        if len(self.symbol_list)>1:
            comb_index = data[most_data_symbol].index
            # Set all data set with this index
            for i in self.symbol_list:
                data[i] = data[i].reindex(
                    index = comb_index, method="pad"
                )
                data[i].reset_index(inplace=True)
        else:
            data[self.symbol_list[0]].reset_index(inplace=True)
        
        total_size = len(data[self.symbol_list[0]])
        self.bar_index = total_size - outsample_size -1
        print(data[self.symbol_list[0]][self.bar_index:self.bar_index+5])
        return data

    def construct_latest_symbol_data(self):
        """
        Creates a dataframe with column open, high, low, close, volumn and 
        symbol id as index
        """
        col_val = []
        for i in self.symbol_list:
            col_val.append(float("nan"))
        d = pd.DataFrame(
            {
                "price_date": col_val
                , "open_price": col_val
                , "high_price": col_val
                , "low_price": col_val
                , "close_price": col_val
                , "volume": col_val
            }
            , index = self.symbol_list
        ) 

        return d


    # ================================#
    # DATA HANDLER DATETIME CONTROL 
    # ================================#    
    def set_handler_datetime(self, startdate, enddate):
        """Replace self.cur_datetime with date"""
        self.start_date = startdate
        self.end_date = enddate
        self.symbol_data = self.construct_symbol_data()
        self.latest_symbol_data = self.construct_latest_symbol_data()
    
    def get_datetime(self):
        """returns the current datetime in object"""
        return self.get_latest_bar_datetime(self.symbol_list[0])

    # def set_handler_end_date(self, date):
    #     """
    #     Replace self.handler_end_date
    #     """
    #     self.end_date = date
    #     # Triggers the creation of latest_symbol_data
    #     self.symbol_data = self.construct_symbol_data()
    #     self.latest_symbol_data = self.construct_latest_symbol_data()

    
    # ================================#
    # PRINT CLASS VARIABLES
    # ================================#
    def show_sample_price_data(self):
        """
        Prints the first 10 rows of price data in each item in price data 
        """
        for i in self.symbol_list:
            print( self.symbol_data[i].head(10) )
    
    def show_latest_symbol_data(self):
        """
        Prints the latest_price_bar dataframe
        """
        print(self.latest_symbol_data)

    def show_symbol_data_head(self):
        """
        Prints the first 5 rows of item in each of the data sets in symbol 
        data
        """
        for i in self.symbol_list:
            print(self.symbol_data[i].head(5))

    
    # ================================#
    # DATA HANDLER FUNCTIONS
    # ================================#
    def get_latest_bar(self, symbol_id):
        """
        Returns the last bar updated from latest symbol data
        """
        bar = self.latest_symbol_data.loc[symbol_id]
        return bar

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last n bars starting from data handler's internal
        datetime. Returns n-k if there is less than n bars available 
        sorted descendingly starting from the most recent bar to 
        bar n or (n-k). If the number of bars in symbol_data is less
        than N, try getting N bars from sec_db instead. 
        
        Parameters:
        symbol - The symbol_id of intended security
        N - the number of bars to query 
        """
        try:
            bar = self.symbol_data[symbol].loc[
                self.bar_index + 1 -N : self.bar_index,
                [
                    "price_date", "open_price", "high_price", "low_price"
                    , "close_price", "volume"
                ]
            ]
            bar.set_index("price_date", inplace=True)

            # If symbol_data has less than N bars, try pulling data from sec_db
            if len(bar) < N:
                try:
                    print("Not enough data loaded, going to sec_db to find data")
                    query = """(SELECT price_date, open_price, high_price, low_price
                        , close_price, volume FROM daily_price WHERE symbol_id =%s
                        AND DATE(price_date) <= '%s' ORDER BY price_date DESC 
                        LIMIT %s) ORDER BY price_date
                        DESC""" %(symbol, self.get_latest_bar_datetime(symbol), N)
                    return pd.read_sql_query(
                        query, con=self.sec_db_conn).loc[::-1].set_index(
                        'price_date')
                except:
                    return bar
            else:
                return bar
        except KeyError:
            print("Unable to obtain latest n bars.")
            raise

    def get_latest_bar_datetime(self, symbol):
        """
        Returns a python datetime object of the most recent bar for a given
        symbol found in latest_symbol_data
        """
        try:
            return self.get_latest_bar_value(symbol, 'price_date')
        except KeyError:
            print("That symbol is not available in the data set.")
            raise
        
    def get_latest_bar_value(self, symbol, val_type):
        """
        Returns one of the Open, High, Low, Close, Volume or OI
        from the last bar.
        """
        return self.symbol_data[symbol].loc[self.bar_index, val_type]
    
    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Returns the last N bar values from the
        latest_symbol list, or N-k if less available.
        """
        try:
            bars = self.symbol_data[symbol].loc[
                self.bar_index +1 - N : self.bar_index, val_type
            ]
            # If symbol_data has less than N bars, try pulling data from sec_db
            if len(bars) < N:
                print("Not enough data loaded, going to sec_db to find data")
                try:
                    query = """(SELECT price_date, %s FROM daily_price WHERE 
                        symbol_id =%s AND DATE(price_date) <= '%s' ORDER BY 
                        price_date DESC LIMIT %s) ORDER BY price_date
                        DESC""" %(val_type, symbol, self.get_latest_bar_datetime(symbol), N)
                    bar_vals = pd.read_sql_query(query, con=self.sec_db_conn).loc[::-1]
                    return bar_vals[val_type]   
                except:
                    return bars     
            else:
                return bars
        except KeyError:
            print('Unable to obtain latest n bars. Data not found.')
            raise


    # ===============================
    # CORPORATE ACTION HANDLER
    # ===============================
    def get_latest_bar_split(self, symbol):
        '''Returns a number representing the stock split on that day
        if any was applied to the security. 
        ''' 
        action_date = self.get_latest_bar_datetime(symbol)

        query = '''SELECT split_ratio FROM daily_corporate_action
        WHERE symbol_id = '%s' AND action_date = '%s' 
        ''' %(symbol, action_date)
        bar = pd.read_sql_query(query, con=self.sec_db_conn)
        
        if bar.empty == False:
            return bar.loc[0, 'split_ratio']
        else: 
            # If no data is found assume no split was given that day
            return 1
    

    def get_latest_bar_dividend(self, symbol):
        '''Returns a number representing the dividends pershare issued on that 
        day. 
        '''
        action_date = self.get_latest_bar_datetime(symbol)

        sql = '''SELECT dividend FROM daily_corporate_action
        WHERE symbol_id = '%s' AND action_date = '%s' 
        ''' %(symbol, action_date)
        bar = pd.read_sql_query(sql, con=self.sec_db_conn)
        
        if bar.empty == False:
            return bar.loc[0, 'dividend']
        else: 
            # If no data is found assume no dividend was given that day
            return 0

    
    # =====================================
    # Execution Handler Function
    # ===================================== 
    def get_next_open_price(self, symbol):
        """Returns the open price of the next bar for a given
        symbol
        """
        try:
            return self.symbol_data[symbol].loc[self.bar_index+1, "open_price"]
        except:
            print('Unable to obtain next open price. Data not found.')
            raise


    # =====================================
    # UPDATE BARS - MARKET EVENT GENERATOR
    # =====================================
    def update_bars(self):
        """
        Pushes the latest bars to the bars_queue for each symbol
        in a tuple OHLCVI format: (datetime, open, high, low,
        close, volume/ open interest).
        """
        next_index = self.bar_index +1 
        for s in self.symbol_list:
            try:
                bar = self.symbol_data[s].loc[next_index]
            except KeyError:
                self.continue_backtest = False
            else:
                if bar.empty is False:
                    self.latest_symbol_data.loc[s, "price_date"] = (
                        bar.loc["price_date"]
                    )
                    self.latest_symbol_data.loc[s, "open_price"] = (
                        bar.loc["open_price"]
                    )
                    self.latest_symbol_data.loc[s, "high_price"] =(
                        bar.loc["high_price"]
                    )
                    self.latest_symbol_data.loc[s, "low_price"] = (
                        bar.loc["low_price"]
                    )
                    self.latest_symbol_data.loc[s, "close_price"] = (
                        bar.loc["close_price"]
                    )
                    self.latest_symbol_data.loc[s, "volume"] = (
                        bar.loc["volume"]
                    )
        if self.continue_backtest is True:
            self.events.put(MarketEvent())
            self.bar_index += 1