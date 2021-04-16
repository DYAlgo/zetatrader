#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# xtb_book.py
# @author: Darren
import time
import datetime as dt
from math import floor
from zetatrader.event import OrderEvent
from zetatrader.book.base import AbstractBook

def fromtimestamp(x):
    return dt.datetime.fromtimestamp(x)

class XtbBook(AbstractBook):
    """Class to provide trading book interface with XTB trading account. 
    This class acts as a ledger while the algorithm is running to track 
    trades and account changes bar by bar. CURRENTLY ONLY WORKS FOR 
    COMMODITIES CFD. 
    """
    def __init__(self, events, bars, connection):
        self.bars = bars
        self.events = events
        self.connection = connection
        self.symbol_list = self.bars.symbol_list
        self.symbol_info = self.construct_symbol_info()
        self.cmd_dict = {0 : 1, 1 : -1}
        self.position_type = {0: 'BUY', 1 : 'SELL'}
        self.account_currency = self.get_account_currency()
        self.equity = self.get_equity()
        self.balance = self.get_balance()
        self.total_margin = self.get_margin()
        self.all_holdings = []
        # Get Current Portfolio Position
        self.current_lots = None
        self.current_positions = None
        self.current_holdings = None
        self.current_margins = None
        self.current_notional = None
        self.net_exposure = None # TODO: Store margins with +- signs.
        
        # SETUP INITIAL PORTFOLIO
        self.construct_current_book()

    def round_down(self, volume, lot_size):
        return floor(volume*(1/lot_size))/(1/lot_size)

    def get_account_currency(self):
        """[summary]
        """
        acc_info = self.connection.get_account_info()
        return acc_info['currency']

    def get_equity(self):
        """Retrives the equity value of the account 
        """
        acc_info = self.connection.get_account_info()
        return acc_info['equity']
    
    def get_balance(self):
        """Retrives the balance of account. 
        """
        acc_info = self.connection.get_account_info()
        return acc_info['balance']
    
    def get_margin(self):
        acc_info = self.connection.get_account_info()
        return acc_info['margin']
    
    # ==================================================== #
    # Portfolio Constructor/Getter
    # ==================================================== #
    def construct_symbol_info(self):
        d = {}
        for symbol in self.symbol_list:
            d[symbol] = self.connection.get_symbol_info(symbol, False)
            d[symbol]['tick_value'] = d[symbol]['tickValue'] # For Risk Manager
            d[symbol]['tick_size'] = d[symbol]['tickSize'] # For Risk Manager
            time.sleep(0.2)
        return d
    
    def construct_current_book(self):
        """Constructs the initial position, holdings and margin values.
        """
        # Get most up-to-date open lots
        self.current_lots = self.get_current_lots()

        # Update Current Position using current lots
        self.current_positions = self.construct_current_position()
        # # Construct Current Notional 
        # Construct Current Holdings
        self.current_holdings = self.construct_current_holdings()
        # Construct Current Margin
        print('Initial Portfolio Constructed') 

    def construct_current_position(self):
        """
        Contructs a dictionary for total volume of each trade.  
        """
        d = {}
        for i in self.symbol_list:
            d[i] = 0
            all_lot_id = list(self.current_lots[i].keys())
            if all_lot_id:
                for l in all_lot_id:
                    lot = self.current_lots[i][l]
                    d[i] += lot['direction'] * lot['volume']
        return d

    def get_current_lots(self):
        """Populates a dictionary with lot information from brokerage account"""
        open_trades = self.connection.get_open_positions()
        d = {}
        # Create position dict
        for i in self.symbol_list:
            d[i] = {}

        # Store lot by symbols in position dict
        if not open_trades:
            return d 
        for lot in open_trades:
            symbol = lot['symbol']
            # close_price > 0 only for open trades, 0 is for pending trades
            if lot['close_price'] > 0 and symbol in self.symbol_list:
                d[symbol][lot['position']] = {
                    'position_type': self.position_type[lot['cmd']], 
                    'direction': self.cmd_dict[lot['cmd']], 
                    'trade_price': lot['open_price'],
                    'trade_date': fromtimestamp(lot['open_time']/1000),
                    'volume': lot['volume'],
                    'profits': lot['profit']# In Account Currency
                }
        return d
    
    def construct_current_holdings(self):
        """Updates current holdings with Margin Values of Each symbol.
        """
        d = {i: 0 for i in self.symbol_list}
        for symbol in self.symbol_list:
            volume = self.current_positions[symbol]
            d[symbol] = self.connection.get_margin_requirement(symbol, abs(volume))
            time.sleep(0.5) # To prevent flooding API
        d['total'] = self.equity
        d['cash'] = self.equity - self.total_margin
        return d

    def construct_current_notional(self):
        """Updates Holdings Value as Net Margin value based on the 
        position information in current_positions. 
        """
        d = {}
        for symbol in self.symbol_list:
            volume = self.current_positions[symbol]
            if volume != 0:        
                fx_rate = 1
                symbol_info = self.connection.get_symbol_info(symbol, False)
                mid_price = (symbol_info['ask'] + symbol_info['bid'])/2 
                quote_currency = symbol_info['currencyProfit']
                contract_size = symbol_info['contractSize']
                if quote_currency == 'USD' and self.account_currency == 'GBP':
                    gbpusd_info = self.connection.get_symbol_info('GBPUSD', False)
                    fx_rate = 1/((gbpusd_info['ask'] + gbpusd_info['bid'])/2)                 
                d[symbol] = fx_rate * contract_size * volume * mid_price
            else:
                d[symbol] = 0
        return d
    
    def construct_current_margin(self):
        total_margin = 0
        d = {i: 0 for i in self.symbol_list}
        for symbol in self.symbol_list:
            volume = 0
            lots = self.current_positions[symbol]
            lot_ids = list(lots.keys())
            if lot_ids:
                for l in lot_ids:
                    volume += lots[l]['volume']
                d[symbol] = self.connection.get_margin_requirement(symbol, volume)
                time.sleep(0.2) # To prevent flooding API
                total_margin += d[symbol]
        d['total'] = self.equity
        d['cash'] = self.equity -total_margin
        return d

    def construct_net_exposure(self):
        pass

    # ==================================================== #
    # Update Portfolio Index, Value, and Position
    # ==================================================== #
    def update_timeindex(self):
        """Updates Snapshot of position value and information
        """
        # Update Account Value
        account_info = self.connection.get_account_info()
        self.equity = account_info['equity'] 
        self.balance = account_info['balance']
        self.total_margin = account_info['margin']

        # Store Previous Margin and Holdings Info
        self.all_holdings.append(self.current_holdings)

        # Update Current lots, then position, then holdings. 
        self.current_lots = self.get_current_lots()
        self.current_positions = self.construct_current_position()
        time.sleep(0.2)
        self.current_holdings = self.construct_current_holdings()

    # ==================================================== #
    # Position Manager
    # ==================================================== #
    def add_position(self, symbol, units, pos_dir):
        """
        Add more volume in the current symbol direction. Use 'BUY' or 
        'SELL' in pos_dir to indicate trade direction.
        """
        lot_size = self.symbol_info[symbol]['lotMin']
        current_pos = self.current_positions[symbol] 
        if current_pos >= 0 and pos_dir == 'BUY':
            fill_size = self.round_down(units, lot_size=lot_size)
            margin_req = self.connection.get_margin_requirement(symbol, fill_size)
            if margin_req < self.equity - self.total_margin:
                order = OrderEvent(symbol, 'MKT', fill_size, 'BUY', 0, isexit=False)
                self.events.put(order)
            else:
                print('Not enough Cash to meet positions margin requirement to trade')
        elif current_pos <= 0 and pos_dir == 'SELL':
            fill_size = self.round_down(units, lot_size=lot_size)
            order = OrderEvent(symbol, 'MKT', fill_size, 'SELL', 0, isexit=False)
            self.events.put(order)
        else:
            raise('Current Position and Units must have same signs.') 

    def reduce_positon(self, symbol, units):
        """
        Reduce the total volume held in current symbol direction. 
        """
        lot_size = self.symbol_info[symbol]['lotMin']
        current_pos = self.current_positions[symbol] 
        if current_pos == 0:
            raise('Unable to reduce position when current position is 0')
        elif units <= 0:
            raise('Units cannot be must be larger than 0')
        else:
            if current_pos > 0 and current_pos >= units:
                # SELL OUT
                fill_dir = 'SELL'
                current_pos = abs(current_pos)
            elif current_pos < 0 and current_pos >= units:
                # BUY BACK
                fill_dir = 'BUY'
        
        if fill_dir == 'BUY' or fill_dir == 'SELL' :
            all_lot_id = list(self.current_lots[symbol].keys())
            for i in all_lot_id:
                if units > 0:
                    qty = 0
                    volume = self.current_lots[symbol][i]['volume']
                    if volume <= units:
                        # Exit lot i
                        qty = self.round_down(volume, lot_size=lot_size)
                        units = units - qty
                    else:
                        # Partial Exit of lot i
                        qty = self.round_down(units, lot_size=lot_size)
                        units = 0    

                    order = OrderEvent(symbol, 'MKT', qty, fill_dir, lot_id=i
                        , isexit=True)
                    self.events.put(order)   
        
    def close_position(self, symbol):
        """Close all lots for a given symbol.

        Args:
            symbol (str): symbol to trade
        """
        all_lot_id = list(self.current_lots[symbol].keys())
        if all_lot_id:
            for i in all_lot_id:
                direction = self.current_lots[symbol][i]['direction']
                if direction > 0:
                    direction = 'SELL'
                else:
                    direction = 'BUY'
                lot_size = self.current_lots[symbol][i]['volume']
                order = OrderEvent(
                    symbol
                    , 'MKT'
                    , lot_size
                    , direction
                    , lot_id=i
                    , isexit=True)
                self.events.put(order)
