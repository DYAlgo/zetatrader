#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# AbstractStrategy.py
# Darren Jun Yi Yeap V0.1

from abc import ABCMeta, abstractmethod

class AbstractStrategy:
    """Abstract class that provides an interface for all subsequent strategy
    handling objects. A Strategy object is meant to generate Signal objects 
    for each particularly symbol given based on the input data such as price.

    This is designed to work both with historical backtesting and live trading.  
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self):
        """
        Provides the mechanisms to calculate the list of signals.
        """
        raise NotImplementedError("Should implement calculate_signals()")
    