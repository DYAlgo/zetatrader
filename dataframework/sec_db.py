#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# sec_db.py
# Author: Darren Jun Yi Yeap
# Version 0.1

import pymysql
import pandas as pd
from data_framework.credentials import sec_db_cred
# Start fixing here. It might be worth rewriting some sections of code


class SEC_DB:
    """
    A sec_db database data handler which allows user the ability to interface
    with sec_db through functions that generate a query from the database.  
    """
    def __init__(self):
        """
        Initialized the sec_db object
        """
        self.sec_db_password = sec_db_cred
        self.con = pymysql.connect(
            host = self.sec_db_password['db_host']
            , user = self.sec_db_password['db_user']
            , passwd = self.sec_db_password['db_pass']
            , db = self.sec_db_password['db_name']
        )
    
    def get_ticker(self, symbol_id):
        '''Returns the ticker from the given symbol_id'''
        sql = """SELECT ticker FROM symbol WHERE
            id = '%s'""" %(symbol_id)
        return (pd.read_sql_query(sql, con = self.con)).iloc[0,0]

    def get_symbol_id(self, ticker):
        '''Returns all symbol id for to the given ticker'''
        sql = """SELECT id FROM symbol WHERE ticker = '%s' ORDER BY
            name ASC"""%(ticker)
        return pd.read_sql_query(sql, con = self.con)
    
    def get_all_symbol_id(self):
        """
        Gets a dataframe of symbol ids from sec_db
        """
        query = """SELECT id FROM symbol ORDER BY id ASC"""    
        return pd.read_sql_query(query, con = self.con)

    def get_us_equity_symbols(self):
        """Gets the symbols for equities in 
        AMEX, NASDAQ, and NYSE exchange"""
        nyse_id = self.get_exchange_id('NYSE')
        nasdaq_id = self.get_exchange_id('NASDAQ')
        amex_id = self.get_exchange_id('AMEX')
        exchanges = (nyse_id, nasdaq_id, amex_id)
    
        sql = """SELECT id FROM symbol WHERE 
            exchange_id in %s 
            ORDER BY id ASC""" %(str(tuple(exchanges)))
        return pd.read_sql_query(sql, con = self.con)

    def get_all_vendors(self):
        '''Returns a table of all the data vendors we have'''
        sql = """SELECT* FROM data_vendor"""
        return pd.read_sql_query(sql, con = self.con)

    def get_data_vendor_id(self, vendor_name):
        '''Return the id for the vendor'''
        sql = """SELECT id FROM data_vendor WHERE name = '%s'
            """ %(vendor_name)
        return (pd.read_sql_query(sql, con = self.con)).iloc[0,0]

    def get_exchange_id(self, exchange_abbreviation):
        '''Return the id for a particular exchange'''
        sql = """SELECT id FROM exchange WHERE abbrev = '%s'
            """ %(exchange_abbreviation)
        return (pd.read_sql_query(sql, con = self.con)).iloc[0,0]

    def get_sector_list(self):
        '''Returns a list of industries in symbol table'''
        sql = """SELECT DISTINCT sector FROM symbol ORDER BY 
            sector ASC"""
        return pd.read_sql_query(sql, con = self.con)

    def get_symbols_by_earliest_date(self, date_time):
        '''Returns a table of securities with the daily data
        available earlier than the given date or at the 
        given date'''
        sql = ''' SELECT DISTINCT symbol_id FROM daily_price 
            WHERE price_date <= '%s'
            ORDER BY symbol_id ASC''' %(date_time)
        id_set = pd.read_sql_query(sql, con = self.con)

        target_list = tuple(id_set['symbol_id'])
        target_list = str(target_list)

        sql = '''SELECT* FROM symbol WHERE id in %s ORDER BY 
            industry''' %(target_list)
        return pd.read_sql_query(sql, con = self.con)

    def get_symbols_from_given_ids(self, id_list):
        '''Returns a table of symbols from the id_list'''
        sql = '''SELECT* FROM symbol WHERE id in %s ORDER BY 
            industry''' %(str(tuple(id_list)))
        pd.set_option('display.width', 500)
        return pd.read_sql_query(sql, con = self.con)

    def get_symbols_by_ticker(self, ticker):
        """
        Returns the all matching tickers found in symbol
        """
        sql = """SELECT id FROM symbol WHERE ticker = '%s' ORDER BY
            name ASC"""%(ticker)
        return pd.read_sql_query(sql, con = self.con)

    def get_symbols_by_sector(self, sector_name):
        '''Returns all stocks within the given sector name
        available in symbol table'''
        sql = ''' SELECT* FROM symbol WHERE sector = '%s'
            ORDER BY industry ASC''' %(sector_name)
        pd.set_option('display.width', 500)
        return pd.read_sql_query(sql, con = self.con)

    def get_symbols_by_industry(self, industry_name):
        '''Returns all stocks within the given industry name
        available in symbol table'''
        sql = ''' SELECT* FROM symbol WHERE industry = '%s'
            ORDER BY industry ASC''' %(industry_name)
        return pd.read_sql_query(sql, con = self.con)  

    # The section below covers functions that returns time series data

    def get_all_bars(self, symbol_id):
        sql = """SELECT price_date, open_price, high_price, low_price,
            close_price FROM daily_price WHERE symbol_id = '%s'
            ORDER BY price_date ASC"""%(symbol_id)
        return pd.read_sql_query(sql, con = self.con)

    def get_bars(self, symbol_id, start_date, end_date):
        '''Returns the data frame of the given symbol id 
        within the given date'''
        sql = """(SELECT price_date, open_price, high_price, low_price,
            close_price FROM daily_price WHERE symbol_id = %s 
            AND price_date BETWEEN '%s' AND '%s' ) ORDER BY
            price_date ASC""" % (symbol_id, 
            start_date, end_date)
        return pd.read_sql_query(sql, con = self.con)

    def get_all_bar_values(self, symbol_id, val_type):
        """Returns all specified data from sec_db"""
        sql = """(SELECT price_date, %s FROM daily_price WHERE
            symbol_id = '%s') ORDER BY
            price_date ASC""" % (val_type, symbol_id)
        return pd.read_sql_query(sql, con = self.con)

    def get_bar_values(self, symbol_id, start_date, end_date, val_type):
        """Returns choice of data from sec_db between the start and
        end date"""
        sql = """(SELECT price_date, %s FROM daily_price WHERE
            symbol_id = '%s' AND price_date BETWEEN
            '%s' AND '%s' ) ORDER BY
            price_date ASC""" % (val_type, symbol_id, start_date, 
            end_date)
        return pd.read_sql_query(sql, con = self.con)

    def get_all_adjusted_bars(self, symbol_id):
        '''Returns the data frame of the given symbol id 
        with its data data adjusted for dividend and split
        effects'''
        ori_data = self.get_all_bars(symbol_id)
        price_data = ori_data[['open_price', 'high_price', 'low_price'
            , 'close_price']]
        
        scalars = self.get_all_bar_values(symbol_id
            , 'adj_close_price')['adj_close_price']/\
            price_data['close_price']
        
        adj_dat = (price_data.transpose()*scalars).transpose()
        
        return pd.concat([ori_data['price_date'], adj_dat], axis = 1)

    def get_adjusted_bars(self, symbol_id, start_date, end_date):
        '''Returns the data frame of the given symbol id 
        within the given date with its data adjusted for dividend 
        and split effects'''
        ori_data = self.get_bars(symbol_id, start_date, end_date)
        price_data = ori_data[['open_price', 'high_price', 'low_price'
            , 'close_price']]
        
        scalars = self.get_bar_values(symbol_id, start_date, end_date
            , 'adj_close_price')['adj_close_price']/\
            price_data['close_price']
        
        adj_dat = (price_data.transpose()*scalars).transpose()
        
        return pd.concat([ori_data['price_date'], adj_dat], axis = 1)

    def get_latest_bar(self, symbol_id, vendor_id = None):
        """
        Returns the latest bar from daily_price using the given id
        """
        if vendor_id is None:
            sql = """SELECT price_date, open_price, high_price, low_price,
                    close_price FROM daily_price WHERE symbol_id = '%s'
                    ORDER BY price_date DESC LIMIT 1 """%(symbol_id)
            return pd.read_sql_query(sql, con = self.con) 
        elif vendor_id is not None:
            sql = """SELECT price_date, open_price, high_price, low_price,
                    close_price FROM daily_price WHERE symbol_id = '%s'
                    AND data_vendor_id = %s ORDER BY 
                    price_date DESC LIMIT 1 """%(symbol_id, vendor_id)
            return pd.read_sql_query(sql, con = self.con) 
    
    # Below holds more analytical functions for using sec_db

    def get_latest_bars_values(self, symbol_id, val_type, N =1, date = 0):
        """
        Returns the last N bar values from the
        latest_symbol list, or N-k if less available in the form of pandas
        dataframe of [datetime, value].
        """
        if date == 0:
            sql = """(SELECT price_date, %s FROM daily_price WHERE
                symbol_id = '%s' ORDER BY price_date DESC) 
                LIMIT %s""" % (val_type, symbol_id, N)
            return pd.read_sql_query(sql, con = self.con).loc[::-1].set_index(
                'price_date')
        else:
            sql = """(SELECT price_date, %s FROM daily_price WHERE
                symbol_id = '%s' AND DATE(price_date) <= '%s' ORDER BY 
                price_date DESC) LIMIT %s 
                """ % (val_type, symbol_id, date, N)
            return pd.read_sql_query(sql, con = self.con).loc[::-1].set_index(
                'price_date')

    # Below are some useful functions that plot time series graphs
    # def plot_security(self, id):
    #     """
    #     Plots a candlestick graph of a given security.
    #     """
    #     price = self.get_all_bars(id)
    #     charts.plot_candlestick(price).show()


if __name__ == "__main__":
    # Create sample securities database connection object
    secdb = SEC_DB()
    for i in list([1,2,3,4,5]):
        print(secdb.get_ticker(i))