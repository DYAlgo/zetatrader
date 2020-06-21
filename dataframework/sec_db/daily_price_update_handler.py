#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import pymysql
import pandas as pd
import datetime as dt 
from dataframework.sec_db.secdb_conn import SecDbConn
from dataframework.tiingo import Tiingo
from dataframework.sec_db.sec_db_data_handler import SecDbDataHandler

class DailyPriceUpdateHandler(SecDbConn):
    """daily drice table update handler class 
    """
    def __init__(self, secdb_handler=None, tiingo_handler=None):
        """Updatesthe daily_price table in sec_db by adding new or updating 
        existing data from our different data sources. 

        Arguments:
            SecDbConn {Connection obj}

        Keyword Arguments:
            max_updates {int} -- maximum number of updates allowed 
                (default: {1})
            starting_id {int} -- symbol id to start finding updates 
                (default: {0})
        """
        super(DailyPriceUpdateHandler, self).__init__()
        self.secdb_handler=secdb_handler
        self.tiingo_handler=tiingo_handler

        self.init_obj()

    def init_obj(self):
        if self.secdb_handler is not None:
            # Initialize the class
            self.secdb_handler=self.secdb_handler()
        
        if self.tiingo_handler is not None:
            # Initialize the class
            self.tiingo_handler=self.tiingo_handler()

    def update_daily_price_from_tiingo(self, id_list=[], max_updates=1):
        """
        
        Keyword Arguments:
            id_list {list} -- list of symbol id to update (default: {[]})
            max_updates {int} -- number of symbol update allowed (default: {1})
        """
        update_count=0
        today=dt.datetime.today().date() # Today's date
        instrument=str('Equities')
        vendor_id = int(self.secdb_handler.get_data_vendor_id(vendor_name='Tiingo'))

        for i in id_list:
            if update_count<max_updates:
                # Get symbol ticker
                ticker=self.secdb_handler.get_ticker(i)
                latest_dt=self.secdb_handler.get_latest_daily_value(
                    i,'price_date'
                )
                now=dt.datetime.now() #Approx time of update/change

                if latest_dt is None:
                    # Request all its historical data
                    df=self.tiingo_handler.get_all_data(ticker, 'daily')

                    if df.empty == False:
                        data_set = []
                        action_set = []

                        for j in df.itertuples(index=False):
                            data_set.append((0, vendor_id, int(i)
                                , j[0].to_pydatetime()
                                , now, now, j[1], j[2], j[3]
                                , j[4], j[5], j[6])
                            )
                            action_set.append((0, vendor_id, int(i),
                                j[0].to_pydatetime(), now, now
                                , j[7], j[8])
                            )

                        # Append these data to sec_db
                        insert_daily_price = """INSERT daily_price (
                            id, data_vendor_id, symbol_id
                            , price_date, created_date
                            , last_updated_date, open_price
                            , high_price, low_price
                            , close_price, adj_close_price
                            , volume) VALUES (%s)""" % (
                                ("%s, " * 12)[:-2]
                            )
                            
                        insert_corp_action = """INSERT 
                        daily_corporate_action (
                        id, data_vendor_id, symbol_id, action_date
                        , created_date, last_updated_date, dividend
                        , split_ratio) VALUES (%s)""" % (("%s, " * 8)[:-2])

                        update_symbol_datetime = """UPDATE symbol SET \
                            last_updated_date = (%s) WHERE id = (%s)"""

                        # Insert data into secdb 
                        try:
                            super().open_connection()
                            with self.conn:
                                cur=self.conn.cursor()
                                r=cur.executemany(
                                    insert_daily_price, data_set
                                )
                                s=cur.executemany(
                                    insert_corp_action, action_set
                                )
                                t=cur.execute(
                                    update_symbol_datetime, (
                                        now, int(i)
                                    )
                                )
                                self.conn.commit()
                                print("%s data added" %ticker)
                                print("%s rows affected in daily_price" %r)
                                print("%s rows affected in daily_corp_action" %s)
                                print("%s rows affected in symbol" %t)
                            super().close_connection()
                            update_count+=1
                        except self.conn.Error as error:
                            code, message = error.args
                            print('Error code: %s' %code)
                            print('>>>>>>> %s' %message)
                            print('Unable to insert data to Sec Db')
                            super().close_connection()
                    else:
                        print('%s data not found on Tiingo' %ticker)
                elif isinstance(latest_dt, dt.date) and latest_dt.date()==today: 
                    # is todays date, dont update. Save the api call
                    print("%s already up-to-date" %ticker)
                elif isinstance(latest_dt, dt.date) and latest_dt.date()<today: 
                    # is earlier than today
                    up=pd.DataFrame()
                    df=pd.DataFrame()
                    new_update=False

                    # Pull date specified data from Tiingo
                    up=self.tiingo_handler.get_data(
                        ticker
                        , latest_dt.strftime('%Y-%m-%d')
                        , latest_dt.strftime('%Y-%m-%d'),'daily'
                    )
                    nx_date=latest_dt+dt.timedelta(days = 1)
                    df=self.tiingo_handler.get_data(ticker
                        , nx_date.strftime('%Y-%m-%d')
                        , today.strftime('%Y-%m-%d'),'daily'
                    )

                    if up.empty==False and df.empty==False:
                        # If new data is found, add it

                        # Update most recent bar
                        for j in up.itertuples(index=False):
                            update_set_p=(now, j[1], j[2], j[3], j[4]
                                , j[5], j[6], vendor_id, int(i)
                                , latest_dt.to_pydatetime()
                            )
                            update_set_corp=(now, j[7], j[8]
                                , vendor_id, int(i)
                                , latest_dt.to_pydatetime()
                            )   

                            update_dp="""UPDATE daily_price SET \
                                last_updated_date = %s, open_price = %s
                                , high_price = %s, low_price = %s
                                , close_price = %s, adj_close_price = %s
                                , volume = %s WHERE data_vendor_id = %s
                                AND symbol_id = %s AND price_date = %s
                            """
                            update_ca="""UPDATE daily_corporate_action\
                                SET last_updated_date = %s
                                , dividend = %s
                                , split_ratio = %s
                                WHERE data_vendor_id = %s
                                AND symbol_id = %s AND action_date = %s
                            """
                            update_symbol_datetime="""UPDATE symbol SET \
                                last_updated_date = %s WHERE id = %s
                            """

                            # Update sec_db
                        try:
                            super().open_connection()
                            with self.conn:
                                cur=self.conn.cursor()
                                r=cur.execute(
                                    update_dp, update_set_p
                                )
                                s=cur.execute(
                                    update_ca, update_set_corp
                                )
                                t=cur.execute(
                                    update_symbol_datetime, (
                                        now, int(i))
                                )
                                self.conn.commit()
                                print("%s last bar updated" %ticker)
                                print("%s rows affected in daily_price" %r)
                                print("%s rows affected in daily_corp_action" %s)
                                print("%s rows affected in symbol" %t)
                            super().close_connection()
                            new_update=True
                        except self.conn.Error as error:
                            code, message = error.args
                            print('Error code: %s' %code)
                            print('>>>>>>> %s' %message)
                            print('Unable to update data to Sec Db')
                            super().close_connection()
                        
                        # Now add new bars for symbol
                        data_set=[]
                        action_set=[]
                        for j in df.itertuples(index=False):
                            data_set.append((0, vendor_id, int(i)
                                , j[0].to_pydatetime(), now, now, j[1]
                                , j[2], j[3], j[4], j[5], j[6])
                            )
                            action_set.append((0, vendor_id, int(i)
                                , j[0].to_pydatetime(), now, now, j[7]
                                , j[8])
                            )

                            insert_daily_price = """INSERT daily_price (
                                id, data_vendor_id, symbol_id
                                , price_date, created_date
                                , last_updated_date, open_price
                                , high_price, low_price
                                , close_price, adj_close_price
                                , volume) VALUES (%s)""" \
                                % (("%s, " * 12)[:-2])

                            insert_corp_action = """INSERT daily_corporate_action(
                                id, data_vendor_id, symbol_id, action_date
                                , created_date, last_updated_date, dividend
                                , split_ratio) VALUES (%s)""" % (("%s, " * 8)[:-2])

                            update_symbol_datetime = """UPDATE symbol SET \
                                last_updated_date = %s WHERE id = %s""" 

                        try:
                            super().open_connection()
                            with self.conn:
                                cur=self.conn.cursor()
                                r=cur.executemany(
                                    insert_daily_price, data_set
                                )
                                s=cur.executemany(
                                    insert_corp_action, action_set
                                )
                                t=cur.execute(
                                    update_symbol_datetime, (
                                        now, int(i)
                                    )
                                )
                                self.conn.commit()
                                print("%s data added" %ticker)
                                print("%s rows affected in daily_price" %r)
                                print("%s rows affected in daily_corp_action" %s)
                                print("%s rows affected in symbol" %t)
                            super().close_connection()
                            new_update=True
                        except self.conn.Error as error:
                            code, message = error.args
                            print('Error code: %s' %code)
                            print('>>>>>>> %s' %message)
                            print('Unable to insert data to Sec Db')
                            super().close_connection()
                    if new_update==True:
                        # print("""%s data updated""" %(ticker))
                        update_count+=update_count
     
                else:
                    # Investigate what data is missing 
                    print("Something is wrong, no data can be updated")
                    print('Symbol: %s'%i)
                    print('latest bar date: %s'%latest_dt)
                    print('')
            else:
                break
        return update_count

    def update_nasdaq_daily_price(self, source=None):
        """Obtain a list of nasday symbol id and call update_daily_price_from_x
        to update nasdaq symbol prices
        
        Keyword Arguments:
            source {[str]} -- Data vendor name (default: {None})
        """
        if source=='Tiingo':
            # Get list of nasdaq securities
            pass

            # Pass that list of securities into the price updater
        else:
            print('No %s source function found' %source)


if __name__ == "__main__":
    # Try updating 3m data 
    ud=DailyPriceUpdateHandler(SecDbDataHandler, Tiingo)
    ud.update_daily_price_from_tiingo([312],1)
