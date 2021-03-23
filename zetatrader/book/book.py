#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# Book.py
# Darren Jun Yi Yeap V0.1

from zetatrader.book.base import AbstractBook

class Book(AbstractBook):
    """Class to provide trading book interface for backtest
    sessions to keep track of all positions and holdings - bar by bar. 
    
    This object can be used by money management and risk management 
    object in portfolio to affect risk and money management decisions.

    More importantly, it acts as a ledger(source of truth) for the
    holdings within a portfolio. The Book class stores the cash and 
    total market holdings value of each symbol for a particular 
    time-index, as well as the percentage change in 
    portfolio total across bars. The book class will also adjust for
    dividends and splits recieved during each bar or tick.    
    """
    def __init__(self, initial_capital, bars, session_type):
        """Initialize Book object. 
        
        Arguments:
            bars {Obj} -- Price Handler object
            events {Obj} -- The Event Queue object.
            session_type {Str} -- String stating session type 
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.session_type = session_type

        self.initial_capital = initial_capital
        self.all_positions = self.construct_all_positions()
        self.current_positions = self.construct_current_position()
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

 
    # ==================================================== #
    # Portfolio Constructors
    # ==================================================== #
    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date
        to determine when the time index will begin.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        d['datetime'] = self.bars.start_dt
        return [d]

    def construct_current_position(self):
        """Constructs the current position list to keep track of ongoing 
        positions
        """
        # Add code to get position from broker if trading session is live
        d = dict( 
            (k,v) for k, v in [(s, 0) for s in self.symbol_list] 
        )
        return d 

    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date
        to determine when the time index will begin.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['datetime'] = self.bars.start_dt
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all symbols.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    
    # ==================================================== #
    # Update Portfolio Index, Value, and Position
    # ==================================================== #
    def update_timeindex(self, event=None):
        """
        Adds a new record to the positions matrix for the current 
        market data bar. This reflects the PREVIOUS bar, i.e. all
        current market data at this stage is known (OHLCV). Checks if
        bars 

        Makes use of a MarketEvent from the events queue.
        """
        # Consider dropping event function - not used at all
        latest_datetime = self.bars.get_latest_bar_datetime()
        # Update positions
        # ================
        dp = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dp['datetime'] = latest_datetime

        #Adjust for splits
        if self.bars.frequency == 'daily': 
            for s in self.symbol_list:
                split = self.bars.get_latest_bar_split(s)
                if split != 1.000000 and split >0.000000:
                    print("%s initiate: %s for 1 split" %(s, split))
                    self.current_positions[s] = self.current_positions[s] * \
                        split
                    dp[s] = self.current_positions[s]
                else:
                    dp[s] = self.current_positions[s]

        # Append the current positions
        self.all_positions.append(dp)

        # Update holdings
        # ===============
        dh = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            last_price = self.bars.get_latest_bar_value(s, "close_price")
            if last_price is not None:
                market_value = self.current_positions[s] * last_price              
                dh[s] = self.current_holdings[s] = market_value
                dh['total'] += market_value 
                
                
                # Adjust for dividends
                if self.bars.frequency == 'daily':
                    if self.bars.get_latest_bar_dividend(s) != 0:
                        cash_dividend = (
                            self.bars.get_latest_bar_dividend(s)
                            *
                            self.current_positions[s]
                        )
                        self.current_holdings['cash'] += cash_dividend
                        dh['cash'] += cash_dividend
                        dh['total'] += cash_dividend

                        if self.current_positions[s] > 0:
                            print('%s issues: %s of total dividends' %(s,
                                    self.bars.get_latest_bar_dividend(s)
                                    *
                                    self.current_positions[s]
                                )
                            )
            else:
                dh[s] = self.all_holdings[-1][s]
                dh['total'] += self.all_holdings[-1][s]

        # Append the current and historical holdings
        self.current_holdings['total'] = dh['total']
        self.all_holdings.append(dh)

    
    # ======================
    # FILL/POSITION HANDLING
    # ======================
    def update_positions_from_fill(self, fill):
        """
        Takes a Fill object and updates the position matrix to
        reflect the new position.

        Parameters:
        fill - The Fill object to update the positions with.
        """
        # Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # Update positions list with new quantities
        self.current_positions[fill.symbol] += fill_dir*fill.quantity

    def update_holdings_from_fill(self, fill):
        """
        Takes a Fill object and updates the holdings matrix to
        reflect the holdings value.

        Parameters:
        fill - The Fill object to update the holdings with.
        """
        # Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # Use fill.fill_cost which returns next opens price. 
        # Update holdings list with new quantities
        fill_cost = fill.fill_cost
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        # Take cost amount out from total and add new mv on next bar
        self.current_holdings['total'] -=  fill.commission     

        print(
            '%s %s Order filled - date:%s price:%s size:%s units' %(
                    fill.direction, fill.symbol, self.bars.get_datetime()
                    , fill_cost, fill.quantity
                )
            )  