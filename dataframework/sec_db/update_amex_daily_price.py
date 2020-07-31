#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Updates AMEX daily price table from Tiingo
# Created: Darren Yeap
from dataframework.tiingo import Tiingo
from dataframework.sec_db.daily_price_table_handler import DailyPriceTableHandler
from dataframework.sec_db.sec_db_data_handler import SecDbDataHandler


def update_amex_daily_price(db_handler, tiingo_handler):
    '''Creates a symbol_table_handler object and calls
    the function needed to update daily price for AMEX
    securities 
    '''
    # Create the obj
    pt_handler=DailyPriceTableHandler(db_handler, tiingo_handler)

    # Use the obj to call the update function 
    pt_handler.update_amex_daily_price()

if __name__ == "__main__":
    update_amex_daily_price(SecDbDataHandler, Tiingo)