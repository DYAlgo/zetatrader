#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import pymysql
import pandas as pd 
from dataframework.credentials import sec_db_cred
from dataframework.sec_db.secdb_conn import SecDbConn

class SecDbDataHandler(SecDbConn):
    """sec_db data handler class
    
    Arguments:
        SecDbConn {[type]} -- [description]
    """
    def __init__(self):
        """Initialize the data handler class
        """
        super(SecDbDataHandler,self).__init__()

    # ================================== #
    # Symbol Descriptive Field functions
    # ================================== #
    def get_ticker(self, symbol_id):
        """Returns a str ticker for the given symbol id

        Arguments:
            symbol_id {int} -- symbol id of symbol 
        """
        super().open_connection()
        query=pd.DataFrame()

        try:
            
            with self.conn:
                statement = """SELECT ticker FROM symbol WHERE
                    id = '%s'""" %(symbol_id)
                query=pd.read_sql(statement, con=self.conn)
                
            super().close_connection()
            
        except self.conn.InternalError as e:
            print('Error: %s'%e)
            super().close_connection()
            #Add logging here 
            sys.exit()
        
        if query.empty == False:
            return query.iloc[0,0]
        else:
            return None


    def get_symbol_id(self, ticker, aslist=False):
        """Return a table or list with symbol id and name or a list of symbol id
        
        Arguments:
            ticker {str} -- ticker to match
            aslist {bool} -- to return as list 
        """
        # Return a table with symbol id and name or a list of symbol id
        pass

    def get_all_symbol_id(self, aslist=False):
        # Return a table (or list) of symbol_id in symbol table
        pass

    def get_sectors_list(self):
        pass # Return a list of sectors in symbol table 

    def get_instruments_list(self):
        pass # Return a list of instruments in symbol table 

    def get_symbol_id_by_exchange_id(self, exchange_id, aslist=False):
        """Return a table or list of symbols id for the given exchange id

        Arguments:
            exchange_id {[type]} -- exchange id 

        Keyword Arguments:
            aslist {bool} -- return as list of symbol id 
                (default: {False})
        """
        super().open_connection()
        query=pd.DataFrame()

        try:
            with self.conn:
                statement="""SELECT * FROM symbol WHERE 
                    exchange_id = '%s'
                """ %exchange_id

                query=pd.read_sql(statement, con=self.conn)

            super().close_connection()

        except self.conn.InternalError as e:
            print('Error: %s'%e)
            super().close_connection()
            #Add logging here 
            sys.exit()

        if aslist==False:
            return query
        else:
            return query['id'].to_numpy()


    def get_symbol_table(
        self, ex_id_ls=None, instrument_ls=None, sector_ls=None
    ):
        pass # Return a table which can also have additiontional match 
        #filters based in exchange, instrument, or sector type 

    def get_symbol_with_data_prior(self, latest_data_date, islist=False):
        pass # Returns a symbol table or list that have data earlier than  
    # ================================== #
    # Exchange and Vendor Descriptive 
    # Field functions
    # ================================== #
    def get_exchange_table(self):
        pass #Return the full exchange table 

    def get_exchange_id(self, exchange_abbrv):
        """Return exchange id for given exchange

        Arguments:
            exchange_abbrv {str} -- exchange abbreviation
        """
        super().open_connection()
        query=pd.DataFrame()

        try:
            
            with self.conn:
                statement = """SELECT id FROM exchange WHERE abbrev = '%s'
                    """ %(exchange_abbrv)
                query=pd.read_sql(statement, con=self.conn)
                
            super().close_connection()
            
        except self.conn.InternalError as e:
            print('Error: %s'%e)
            super().close_connection()
            #Add logging here 
            sys.exit()
        
        if query.empty == False:
            return query.iloc[0,0]
        else:
            return None

    def get_data_vendor_table(self):
        pass # Return the full vendor table

    def get_data_vendor_id(self, vendor_name):
        """Return the vendor id for the given vendor name

        Arguments:
            vendor_name {str} -- Vendor name as string 

        Returns:
            Return vendor id which is an integer
        """
        super().open_connection()
        query=pd.DataFrame()

        try: 
            with self.conn:
                statement = """SELECT id FROM data_vendor WHERE name = '%s'
                    """ %(vendor_name)
                query=pd.read_sql(statement, con=self.conn)           
            super().close_connection()
            
        except self.conn.InternalError as e:
            print('Error: %s'%e)
            super().close_connection()
            #Add logging here 
            sys.exit()
        
        if query.empty == False:
            return query.iloc[0,0]
        else:
            return None

    # =========================== #
    # Price data functions
    # =========================== #
    def get_all_daily_bars(self, symbol_id):
        pass # Return a table with open, high, low, close, adj price, and volumn.

    def get_all_daily_price(self, symbol_id ,adjusted=False):
        pass # Return ohlc or adjusted ohlc in a dataframe.

    def get_daily_bars(self, symbol_id, startdate, enddate):
        pass # Return a table with open high low close adj price and volumn 
        # within the start and end date

    def get_daily_price(self, symbol_id, startdate, enddate, adjusted=False):
        pass # Return a table of ohlc or adjusted ohlc in a dataframe

    def get_latest_daily_bar(self, symbol_id):
        pass # Return a dataframe with one or no row of data 

    def get_latest_daily_value(self, symbol_id, val_type):
        """Return the latest value from bar for the given id
        
        Arguments:
            symbol_id {int} -- Symbol id 
        """
        super().open_connection()
        query=pd.DataFrame()

        try:
            
            with self.conn:
                statement = """SELECT %s FROM daily_price 
                    WHERE symbol_id = '%s'
                    ORDER BY price_date DESC LIMIT 1
                    """ %(val_type, symbol_id)
                query=pd.read_sql(statement, con=self.conn)
                
            super().close_connection()
            
        except self.conn.InternalError as e:
            print('Error: %s'%e)
            super().close_connection()
            #Add logging here 
            sys.exit()
        
        if query.empty == False:
            return query.iloc[0,0]
        else:
            return None  
        



if __name__ == "__main__":
    # Create handler
    source=SecDbDataHandler()
    print('NYSE ID: %s' %source.get_exchange_id('NYSE'))
    print(source.get_symbol_id_by_exchange_id(3,True))
    latest_bar_dt=source.get_latest_daily_value(3, 'price_date')
    print(latest_bar_dt.date())
    print(type(latest_bar_dt.date()))
    empty_bar_dt=source.get_latest_daily_value(97997979797, 'price_date')
    print(empty_bar_dt)
    print(source.get_data_vendor_id('Tiingo'))