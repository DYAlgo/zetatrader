#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# symbol_table_handler.py
# Created: Darren Yeap
import pandas as pd
import urllib.request
import numpy as np
import datetime as dt
import pymysql
from dataframework.sec_db.secdb_conn import SecDbConn
from dataframework.credentials import sec_db_cred
from dataframework.sec_db.sec_db_data_handler import SecDbDataHandler
import pymysql as mysql_Connection 


class SymbolTableHandler(SecDbConn):
    """
    Object that contains the functions to update the symbol table in
    sec_db. This object is not suitable for making query regarding 
    values in sec_db, instead this is suitable for pulling newest
    symbol data from external sources (i.e nasdaq.com) which 
    this object has functions that will update these symbols.
    """ 
    def __init__(self, secdb_handler=None):
        """
        Initializes the object
        """
        super(SymbolTableHandler, self).__init__()
        self.sec_db_password = sec_db_cred
        self.secdb_handler=secdb_handler

    def get_amex_symbols(self):
        """
        Returns the official symbol list for AMEX.
        """
        url = (
            'https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&'
            'exchange=%s&render=download'
        ) %('AMEX')

        request = urllib.request.urlopen(url)
        return(pd.read_csv(request))
    
    def get_nasdaq_symbols(self):
        """
        Returns the official symbol list for NASDAQ.
        """
        url = (
            'https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&'
            'exchange=%s&render=download'
        ) %('NASDAQ')

        request = urllib.request.urlopen(url)
        return(pd.read_csv(request))


    def get_nyse_symbols(self):
        """
        Returns the official symbol list for NYSE.
        """
        url = (
            'https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&'
            'exchange=%s&render=download'
        ) %('NYSE')

        request = urllib.request.urlopen(url)
        return(pd.read_csv(request))
    
    def get_arca_etf_symbols(self):
        """
        Return the symbols for ETFs from ARCA exchange. The list of ETF is 
        pulled from NASDAQ's webpage and is verified at NYSE ARCA webpage 
        """
        url = (
            'ftp://ftp.nasdaqtrader.com/symboldirectory/otherlisted.txt'
        )
        request = urllib.request.urlopen(url)
        etf_list = pd.read_csv(request, sep = '|')

        etf_list = etf_list[etf_list.ETF == 'Y']
        etf_list = etf_list[etf_list.Exchange == 'P'] #P for ARCA

        return etf_list

    def get_bzx_symbols(self):
        """Return the symbols from BZX exchange(previously BATS). The list
        is pulled directly from CBOE BZX Exchange webpage.  

        Returns:
            [type]: [description]
        """
        today=dt.datetime.now()
        year=today.year
        month=today.month if len(str(today.month))>1 else '0'+str(today.month) 
        day=today.day-1 if len(str(today.day-1))>1 else '0'+str(today.day-1) 

        url=(
            'https://markets.cboe.com/us/equities/market_statistics/'+
            'listed_securities/'+str(year)+'/'+str(month)+
            '/bzx_equities_listed_security_rpt_'+
            str(year)+str(month)+str(day)+'.txt-dl?mkt=bzx'
        )

        print(url)
        request=urllib.request.urlopen(url)
        etf_list = pd.read_csv(request, sep = '|', skiprows=1)

        return etf_list


    # -------------------------------------------------------------------------
    # -Section below contains functions that are required by obj to function---
    # -------------------------------------------------------------------------

    def check_if_symbol_exist(self, ticker, name, exchange_id):
        """Returns a tuple with True or False and its symbol_id based on 
        whether there is a corresponding symbol that has the ticker or 
        name given in the parameter
        """
        sql = ("""SELECT id FROM symbol WHERE (ticker = "%s") 
        AND (name = "%s") AND (exchange_id = "%s")
        """ %(ticker, name, exchange_id))
        
        super().open_connection()

        try:
            with self.conn:
                matches=pd.read_sql_query(sql, self.conn)

                if len(matches) > 0:
                    key = matches.iloc[0][0]
                    return (True, key)
                else: 
                    return (False, None)
                    
        except:
            print("Error occured during checking symbols existence.")
            return (True, 0)

    # -------------------------------------------------------------------------
    # -The function below contains code for update particular exchanges symbols
    # -------------------------------------------------------------------------

    def update_amex_symbols(self):
        """
        Updates the symbol table in sec_db with the latest symbol infromation
        from NASDAQ webpage
        """
        exchange_abbrv = 'AMEX'
        exchange_id = self.secdb_handler.get_exchange_id(exchange_abbrv)

        latest_list = self.get_amex_symbols()

        # Varify that latest list is still in our recognized format
        if 'Symbol' == latest_list.columns[0]:
            symbol_col = 0
        else:
            raise ('Symbol column not found')
        if 'Name' == latest_list.columns[1]:
            name_col = 1
        else:
            raise ('Name column not found')
        if 'Sector' == latest_list.columns[5]:
            sector_col = 5
        else:
            raise ('Sector column not found')

        rows_to_add = []

        for row in latest_list.itertuples():
            # print(row)
            ticker = row[symbol_col+1]
            com_name  = row[name_col+1]
            now = dt.datetime.today()

            stock_exist = self.check_if_symbol_exist(
                ticker, com_name, exchange_id
            )
            # print(stock_exist) 

            if stock_exist[0] == False:
                # All to a list to be added
                sector = str(row[sector_col+1])                       
                rows_to_add.append(
                    (
                        0, int(exchange_id), str(ticker), str('Equities')
                        , str(com_name), str(sector), str('USD')
                        , now, now
                    )
                )

        # The code below constructs the field for mysql commands
        add_fields = ("id, exchange_id, ticker, instrument, name, sector,"
            " currency, created_date, last_updated_date")
        add_command = """INSERT INTO symbol (%s) VALUES (%s)""" % (add_fields
            , ('%s, ' * 9)[:-2])

        # Add symbols to sec_db
        try:
            super().open_connection()
            with self.conn:
                cur=self.conn.cursor()
                r=cur.executemany(add_command, rows_to_add) 
                self.conn.commit()
                print("%s new AMEX symbols added" %len(rows_to_add))
                print('%s rows affected in symbol' %r)
            super().close_connection()
        except self.conn.Error as error:
            code, message = error.args
            print('Error code: %s' %code)
            print('>>>>>>> %s' %message)
            print('Unable to insert AMEX symbol data to sec_db')
            super().close_connection() 

    def update_nyse_symbols(self):
        """
        Updates the symbol table in sec_db with the latest symbol infromation
        from NASDAQ webpage
        """
        exchange_abbrv = 'NYSE'
        exchange_id = self.secdb_handler.get_exchange_id(exchange_abbrv)

        latest_list = self.get_nyse_symbols()

        # Varify that latest list is still in our recognized format
        if 'Symbol' == latest_list.columns[0]:
            symbol_col = 0
        else:
            raise ('Symbol column not found')
        if 'Name' == latest_list.columns[1]:
            name_col = 1
        else:
            raise ('Name column not found')
        if 'Sector' == latest_list.columns[5]:
            sector_col = 5
        else:
            raise ('Sector column not found')

        rows_to_add = []

        for row in latest_list.itertuples():
            # print(row)
            ticker = row[symbol_col+1]
            com_name  = row[name_col+1]
            now = dt.datetime.today()

            stock_exist = self.check_if_symbol_exist(
                ticker, com_name, exchange_id
            )
            # print(stock_exist) 

            if stock_exist[0] == False:
                # All to a list to be added
                sector = str(row[sector_col+1])                       
                rows_to_add.append(
                    (
                        0, int(exchange_id), str(ticker), str('Equities')
                        , str(com_name), str(sector), str('USD')
                        , now, now
                    )
                )

        # The code below constructs the field for mysql commands
        add_fields = ("id, exchange_id, ticker, instrument, name, sector,"
            " currency, created_date, last_updated_date")
        add_command = """INSERT INTO symbol (%s) VALUES (%s)""" % (add_fields
            , ('%s, ' * 9)[:-2])

        # Add symbols to sec_db
        try:
            super().open_connection()
            with self.conn:
                cur=self.conn.cursor()
                r=cur.executemany(add_command, rows_to_add) 
                self.conn.commit()
                print("%s new NYSE symbols added" %len(rows_to_add))
                print('%s rows affected in symbol' %r)
            super().close_connection()
        except self.conn.Error as error:
            code, message = error.args
            print('Error code: %s' %code)
            print('>>>>>>> %s' %message)
            print('Unable to insert NYSE symbol data to sec_db')
            super().close_connection()

    def update_nasdaq_symbols(self):
        """
        Updates the symbol table in sec_db with the latest symbol infromation
        from NASDAQ webpage
        """
        exchange_abbrv = 'NASDAQ'
        exchange_id = self.secdb_handler.get_exchange_id(exchange_abbrv)

        latest_list = self.get_nasdaq_symbols()

        # Varify that latest list is still in our recognized format
        if 'Symbol' == latest_list.columns[0]:
            symbol_col = 0
        else:
            raise ('Symbol column not found')
        if 'Name' == latest_list.columns[1]:
            name_col = 1
        else:
            raise ('Name column not found')
        if 'Sector' == latest_list.columns[5]:
            sector_col = 5
        else:
            raise ('Sector column not found')

        rows_to_add = []

        for row in latest_list.itertuples():
            # print(row)
            ticker = row[symbol_col+1]
            com_name  = row[name_col+1]
            now = dt.datetime.today()

            stock_exist = self.check_if_symbol_exist(
                ticker, com_name, exchange_id
            )
            # print(stock_exist) 

            if stock_exist[0] == False:
                # All to a list to be added
                sector = str(row[sector_col+1])                       
                rows_to_add.append(
                    (
                        0, int(exchange_id), str(ticker), str('Equities')
                        , str(com_name), str(sector), str('USD')
                        , now, now
                    )
                )

        # The code below constructs the field for mysql commands
        add_fields = ("id, exchange_id, ticker, instrument, name, sector,"
            " currency, created_date, last_updated_date")
        add_command = """INSERT INTO symbol (%s) VALUES (%s)""" % (add_fields
            , ('%s, ' * 9)[:-2])

        # Add symbols to sec_db
        try:
            super().open_connection()
            with self.conn:
                cur=self.conn.cursor()
                r=cur.executemany(add_command, rows_to_add) 
                self.conn.commit()
                print("%s new NASDAQ symbols added" %len(rows_to_add))
                print('%s rows affected in symbol' %r)
            super().close_connection()
        except self.conn.Error as error:
            code, message = error.args
            print('Error code: %s' %code)
            print('>>>>>>> %s' %message)
            print('Unable to insert NASDAQ symbol data to sec_db')
            super().close_connection() 

    def update_arca_etf_symbols(self):
        """
        Pulls in the latest ARCA Traded ETF data and update it to our 
        sec_db symbol list. It will check if the symbol already exist
        , if it does, it will skip it. If not, it will add the symbol 
        to the list. 
        """
        arca_abbrv = 'NYSE ARCA'
        exchange_id = self.secdb_handler.get_exchange_id(arca_abbrv)
        symbol_list = self.get_arca_etf_symbols()

        # Varify that latest list is still in our recognize format
        if 'NASDAQ Symbol' == str(symbol_list.columns[-1]):
            pass
        else:
            raise ('Symbol column not found')
            
        if 'Security Name' == str(symbol_list.columns[1]):
            name_column = 1
        else:
            raise ('Name column not found')
        
        rows_to_add = []

        for row in symbol_list.itertuples():
            ticker = row[-1]
            fund_name = row[name_column+1]
            now = dt.datetime.today()

            stock_exist = self.check_if_symbol_exist(str(ticker)
                , str(fund_name), exchange_id)
            
            if stock_exist[0] == False:
                sector = 'NA'
                rows_to_add.append(
                    (
                        0, int(exchange_id), str(ticker)
                        , str('Exchange Traded Funds'), str(fund_name)
                        , str(sector), 'USD', now, now 
                    )
                )
            
        # This code below constructs the field for MySQL commands
        add_fields = "id, exchange_id, ticker, instrument, name, sector\
            , currency, created_date, last_updated_date"
        add_command = """INSERT INTO symbol (%s) VALUES (%s)""" % (add_fields \
        , ("%s, " * 9)[:-2])

        try:
            super().open_connection()
            with self.conn:
                cur=self.conn.cursor()
                r=cur.executemany(add_command, rows_to_add) 
                self.conn.commit()
                print("%s new ARCA ETF symbols added" %len(rows_to_add))
                print('%s rows affected in symbol' %r)
            super().close_connection()
        except self.conn.Error as error:
            code, message = error.args
            print('Error code: %s' %code)
            print('>>>>>>> %s' %message)
            print('Unable to insert ARCA ETF symbol data to sec_db')
            super().close_connection()

    def update_bzx_exchange_symbols(self):
        """Pulls in the latest list of ETPs traded on the 
        BZX Exchange and update it into the sec_db symbol table.
        Symbols already in symbol table will be skipped.
        """
        bzx_abbrv='CBOE BZX'
        exchange_id=self.secdb_handler.get_exchange_id(bzx_abbrv)
        symbol_list=self.get_bzx_symbols()

        # Varify list is in our intended format
        if 'Symbol'==str(symbol_list.columns[0]):
            pass
        else:
            raise('Symbol column not found')

        if 'Issue Name'==str(symbol_list.columns[1]):
            pass
        else:
            raise('Issue Name column not found')

        if 'Currency'==str(symbol_list.columns[3]):
            pass
        else:
            raise('Currency column not found')

        rows_to_add=[]

        for row in symbol_list.itertuples():
            ticker=row[1]
            fund_name=row[2]
            currency=row[4]
            now=dt.datetime.today()

            stock_exist=self.check_if_symbol_exist(str(ticker)
                , str(fund_name), exchange_id)
            
            if stock_exist[0]==False:
                sector='NA'
                rows_to_add.append(
                    (
                        0, int(exchange_id), str(ticker)
                        , str('Exchange Traded Funds'), str(fund_name)
                        , str(sector), str(currency), now, now
                    )
                )
            
        # SQL Code to add data 
        add_fields="id, exchange_id, ticker, instrument, name, sector\
            , currency, created_date, last_updated_date"
        add_command="""INSERT INTO symbol (%s) VALUES (%s)""" % (add_fields \
            , ("%s, " * 9)[:-2])
        
        try:
            super().open_connection()
            with self.conn:
                cur=self.conn.cursor()
                r=cur.executemany(add_command, rows_to_add) 
                self.conn.commit()
                print("%s new BZX Exchange symbols added" %len(rows_to_add))
                print('%s rows affected in symbol' %r)
            super().close_connection()
        except self.conn.Error as error:
            code, message = error.args
            print('Error code: %s' %code)
            print('>>>>>>> %s' %message)
            print('Unable to insert BZX Exchange symbol data to sec_db')
            super().close_connection()
            

    #--------------------------------------------------------------------------
    #-Below contains functions that combines the functions above to automate---
    #-the sec_db symbol update process-----------------------------------------
    #--------------------------------------------------------------------------

    def update_major_us_exchange_symbols(self):
        """
        Runs the symbol update function for NYSE, NASDAQ, and AMEX
        """
        print('Starting symbol updates for NASDAQ, AMEX, and NYSE')
        self.update_amex_symbols()
        self.update_nasdaq_symbols()
        self.update_nyse_symbols()
        print("Major US exchange (NYSE, AMEX, and NASDAQ) symbols update",
            " complete")


if __name__ == '__main__':
    #Inital symbol_control object
    sym_ctrl = SymbolTableHandler(SecDbDataHandler())
    # sym_ctrl.update_major_us_exchange_symbols()
    # sym_ctrl.update_arca_etf_symbols()
    print(sym_ctrl.check_if_symbol_exist("MMM", "3M Company", 3))
    # sym_ctrl.update_bzx_exchange_symbols()