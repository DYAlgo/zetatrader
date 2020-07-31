#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Updates ARCA daily price table from Tiingo
# Created: Darren Yeap
from dataframework.tiingo import Tiingo
from dataframework.sec_db.daily_price_table_handler import DailyPriceTableHandler
from dataframework.sec_db.sec_db_data_handler import SecDbDataHandler

def update_arca_daily_price(db_handler, tiingo_handler):
    '''Creates a symbol_table_handler object and calls
    the function needed to update daily price for ARCA 
    securities
    '''
    # Create the obj
    pt_handler=DailyPriceTableHandler(db_handler, tiingo_handler)

    # Use the obj to call the update function 
    pt_handler.update_arca_daily_price(source='Tiingo')

if __name__ == "__main__":
    update_arca_daily_price(SecDbDataHandler, Tiingo)