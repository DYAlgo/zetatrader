#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import os
import pymysql
import pandas as pd
import datetime as dt

# Import own modules
from zetatrader.event import MarketEvent
from zetatrader.price_handler.base import AbstractPriceHandler


class DbPriceHandler(AbstractPriceHandler):
    """[summary]"""

    def __init__(
        self,
        events,
        symbol_dict,
        start_dt,
        end_dt,
        db_user=os.environ.get("SEC_DB_USER"),
        db_password=os.environ.get("SEC_DB_PW"),
        frequency="daily",
        data_vendor=6,
    ):
        """Initialize securities_db price handler object.

        Args:
            events ([type]): Event object
            symbol_dict ([type]): dictionary with symbol_id as value and
                ticker as key
            db_user ([type]): securities_db user
            db_password ([type]): securities_db password
        """
        self.events = events
        self.symbol_dict = symbol_dict
        self.symbol_list = list(self.symbol_dict.keys())
        self.bar_index = -1
        self.continue_backtest = True
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.frequency = frequency
        self.data_vendor = data_vendor

        # Connect to securities_db
        self.sec_db_conn = pymysql.connect(
            host="localhost", user=db_user, passwd=db_password, db="securities_db"
        )
        self.symbol_data = self.construct_symbol_data()

    def __str__(self):
        return f"Securities DB Price Handler. Data Vendor ID: {self.data_vendor}"

    # ================================#
    # CONSTRUCTOR
    # ================================#
    def construct_symbol_data(self):
        """Creates a dictionary where each key is a ticker and its values
        the corresponding ticker date, open, high, low, and close as a
        dataframe.
        """
        symbol_data = {}
        max_idn_len = 0
        most_data_symbol = 0

        for symbol in self.symbol_list:
            # Get price data
            q_str = """(SELECT price_date, open_price, high_price, low_price,
            close_price, adj_close_price, volume FROM 
            %s_price WHERE symbol_id = %s AND price_date BETWEEN '%s' 
            AND '%s' AND data_vendor_id = %s) ORDER BY price_date ASC""" % (
                self.frequency,
                self.symbol_dict.get(symbol, 0),
                self.start_dt,
                self.end_dt,
                self.data_vendor,
            )
            price_data = pd.read_sql_query(q_str, con=self.sec_db_conn)
            price_data.set_index("price_date", inplace=True)
            # If EOD Data, standardized time component
            if self.frequency == "daily":
                price_data = price_data.resample("1D").last().dropna(how="all").copy()

            # Check index length comparison
            if len(price_data) > max_idn_len:
                max_idn_len = len(price_data)
                most_data_symbol = symbol
            symbol_data[symbol] = price_data

        if len(self.symbol_list) > 1:
            new_index = symbol_data[most_data_symbol].index
            # Now we need to carry out forward fill every shorter dataset
            for symbol in self.symbol_list:
                symbol_data[symbol] = self.reindex_symbol_data(
                    symbol_data.get(symbol), new_index
                )
        else:
            # Reset index to integer
            symbol_data[self.symbol_list[0]].reset_index(inplace=True)

        return symbol_data

    def reindex_symbol_data(self, df, new_index):
        """Replaces current date index of dataframe with given date index
        and forward fills any missing data under new date index. Finally,
        reset the index as integers and return the dataframe.

        Args:
            df (DataFrame): Dataframe to reindex
            new_index (list): New index for dataframe

        Returns:
            [type]: [description]
        """
        df = df.reindex(index=new_index, method="pad")
        # Reset index to integer
        df.reset_index(inplace=True)
        return df

    # ================================#
    # PRICE HANDLER FUNCTIONS
    # ================================#
    def get_symbolid(self, symbol):
        """[summary]

        Args:
            symbol ([type]): [description]
        """
        return self.symbol_dict.get(symbol)

    def get_latest_bar(self, symbol):
        """Return latest bar

        Args:
            symbol ([type]): [description]

        Returns:
            [type]: pandas series
        """
        return self.symbol_data.get(symbol).loc[self.bar_index]

    def get_latest_bars(self, symbol, n):
        """Returns n most recent bar.

        Args:
            symbol ([type]): [description]
            n ([type]): [description]

        Returns:
            [type]: [description]
        """
        if (n - 1) < self.bar_index:
            bar = self.symbol_data.get(symbol).loc[
                self.bar_index - n + 1 : self.bar_index
            ]
            return bar
        else:
            bar = self.symbol_data.get(symbol).loc[: self.bar_index]
            return bar

    def get_datetime(self, symbol=None):
        return self.get_latest_bar_datetime(symbol)

    def get_latest_bar_datetime(self, symbol=None):
        if symbol == None:
            return self.get_latest_bar(self.symbol_list[0])["price_date"]
        else:
            return self.get_latest_bar(symbol)["price_date"]

    def get_latest_bar_value(self, symbol, val_type):
        """Returns specific field for latest bar"""
        return self.get_latest_bar(symbol)[val_type]

    def get_latest_bar_values(self, symbol, val_type, n=1):
        return self.get_latest_bars(symbol, n)[val_type]

    def update_bars(self):
        """Updated bar index check for existence of next bar. Puts
        market event to queue if next bar is found.
        """
        next_index = self.bar_index + 1
        # Check that every symbol has next price
        for symbol in self.symbol_list:
            try:
                bar = self.symbol_data[symbol].loc[next_index]
            except KeyError:
                self.continue_backtest = False
            else:
                if bar.empty is False:
                    pass
        if self.continue_backtest is True:
            self.events.put(MarketEvent())
            self.bar_index += 1

    # ================================== #
    # CORPORATE ACTION HANDLER
    # ================================== #
    def get_latest_bar_split(self, symbol):
        """Returns a number representing the stock split on that day
        if any was applied to the security.
        """
        if self.frequency == "daily":
            symbol_id = self.symbol_dict.get(symbol)
            action_date = self.get_latest_bar_datetime()

            query = """SELECT split_ratio FROM daily_corporate_action
            WHERE symbol_id = '%s' AND action_date = '%s' AND data_vendor_id = %s
            """ % (
                symbol_id,
                action_date,
                self.data_vendor,
            )
            bar = pd.read_sql_query(query, con=self.sec_db_conn)

            if bar.empty == False:
                return bar.loc[0, "split_ratio"]
            else:
                # If no data is found assume no split was given that day
                return 1
        else:
            raise ("Wrong Frequency called for stock split.")

    def get_latest_bar_dividend(self, symbol):
        """Returns a number representing the dividends pershare issued on that
        day.
        """
        if self.frequency == "daily":
            symbol_id = self.symbol_dict.get(symbol)
            action_date = self.get_latest_bar_datetime()

            sql = """SELECT dividend FROM daily_corporate_action
            WHERE symbol_id = '%s' AND action_date = '%s' AND data_vendor_id = %s
            """ % (
                symbol_id,
                action_date,
                self.data_vendor,
            )
            bar = pd.read_sql_query(sql, con=self.sec_db_conn)

            if bar.empty == False:
                return bar.loc[0, "dividend"]
            else:
                # If no data is found assume no dividend was given that day
                return 0
        else:
            raise ("Wrong Frequency called for dividend.")

    # ================================== #
    # EXECUTION HANDLER FUNCTION
    # ================================== #
    def get_next_open_price(self, symbol):
        """Get the open price of next bar.

        Args:
            symbol (str): [description]
        """
        try:
            return self.symbol_data[symbol].loc[self.bar_index + 1, "open_price"]
        except:
            print("Unable to obtain next open price. Data not found.")
            raise
