#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# AbstractBook.py
# Darren Jun Yi Yeap V0.1

from abc import ABCMeta, abstractmethod

class AbstractBook:
    """
    Abstract base class providing interface of a trading book for all
    subsequent inherited book class (for backtest or live account). The
    objective of book class is to serve as a trading book for a given
    portfolio. A trading book is a ledger that tracks previous positions
    , current positions, previous holdings, and current holdings.    
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def construct_initial_capital(self):
        """Returns the value of initial capital available. 
        """
        raise NotImplementedError("Should implement construct_initial_capital()")

    @abstractmethod
    def construct_all_positions(self):
        """Return list where each position is a dictionary consisting 
        datetime of index and positions for each symbol list  
        """
        raise NotImplementedError("Should implement construct_all_positions()")
    
    @abstractmethod
    def construct_current_position(self):
        """Return dictionary where symbol id is key and values are the 
        positions of the symbol
        """
        raise NotImplementedError(
            "Should implement construct_current_positions()"
        )

    @abstractmethod
    def construct_all_holdings(self):
        """Return list where each position is a dictionary consisting 
        datetime of index and holdings for each symbol list 
        """
        raise NotImplementedError("Should implement construct_all_holdings()")


    @abstractmethod
    def construct_current_holdings(self):
        """Return dictionary where symbol id is key and values are the 
        holdings of the symbol
        """
        raise NotImplementedError("Should implement construct_current_holdings()")
    
    # =================================================== #
    # Update Book Index, Value, and Position 
    # =================================================== #
    @abstractmethod
    def update_timeindex(self):
        """
        Adds new record to all position and holdings record and update
        current holdings and position index. 
        """
        raise NotImplementedError("Should implement update_timeindex()")

    # ======================
    # FILL/POSITION HANDLING
    # ======================
    @abstractmethod
    def update_positions_from_fill(self, fill):
        """Takes a Fill Event and update position matrix to reflect new trade
        
        Arguments:
            fill {Fill Event} -- Fill event object with executed trade details
        """
        raise NotImplementedError(
            "Should implement update_positions_from_fill()"
        )

    @abstractmethod
    def update_holdings_from_fill(self, fill):
        """Takes a Fill Event and update holdings matrix to reflect new trade
        
        Arguments:
            fill {Fill Event} -- Fill event object with executed trade details
        """
        raise NotImplementedError(
            "Should implement update_holdings_from_fill()"
        )

    