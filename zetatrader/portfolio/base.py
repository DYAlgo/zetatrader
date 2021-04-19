#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime as dt
from zetatrader.event import SignalEvent
from abc import ABCMeta, abstractmethod

class AbstractPortfolio:
    """Abstract positions along with position sizing algorithms. 
    """
    __metaclass__ = ABCMeta

    # =================================================== #
    # PORTFOLIO CONSTRUCTION
    # =================================================== #
    @abstractmethod
    def construct_current_position(self):
        """Return dictionary where symbol id is key and values are the 
        positions of the symbol
        """
        raise NotImplementedError(
            "Should implement construct_current_positions()"
        )
        
    @abstractmethod
    def construct_current_holdings(self):
        """Return dictionary where symbol id is key and values are the 
        holdings of the symbol
        """
        raise NotImplementedError("Should implement construct_current_holdings()")

    # ==================================================== #
    # Update Portfolio Index
    # ==================================================== #
    @abstractmethod
    def update_timeindex(self):
        """Updates portfolio with latest information of holdings
        """
        raise NotImplementedError("Should implement update_timeindex()")

    # =================================================== #
    # POSITION MANAGER 
    # =================================================== #
    @abstractmethod
    def add_position(self):
        """Adds to current position of a securities.
        """
        raise NotImplementedError("Should implement add_position()")
    
    def reduce_positon(self):
        """Reduce position of given security
        """
        raise NotImplementedError("Should implement reduce_position()")

    def close_position(self):
        """Close all positions for a given security 
        """
        raise NotImplementedError("Should implement close_position()")