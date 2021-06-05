#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import numpy as np
import datetime as dt

# Import own modules
from zetatrader.strategy.base import AbstractStrategy
from zetatrader.event import SignalEvent


class Strategy(AbstractStrategy):
    def __init__(self, bars, events):
        self.events = events
        self.bars = bars
        self.symbol_list = self.bars.symbol_list

        # Position Tracking
        self.bought = self._calculate_initial_bought()
        self.profit_tgt = {x: 0 for x in self.symbol_list}
        self.stop_loss = {x: 0 for x in self.symbol_list}

    def _calculate_initial_bought(self):
        """[summary]"""
        bought = {}
        for s in self.symbol_list:
            bought[s] = "OUT"
        return bought

    def long_trade(
        self, strat_id, symbol, strength, sizing_type, tgt=np.nan, stop=np.nan
    ):
        """ADD LONG SIGNAL TO EVENT AND UPDATE STRATEGY TRACKING.

        Args:
            ticker ([type]): [description]
            strength ([type]): [description]
            sizing_type ([type]): [description]
        """
        sig_dir = "LONG"
        signal = SignalEvent(
            strat_id, symbol, dt.datetime.now(), sig_dir, strength, sizing_type
        )
        self.events.put(signal)
        self.bought[symbol] = "LONG"

        # SET TARGET AND STOP LOSS
        self.profit_tgt[symbol] = tgt
        self.stop_loss[symbol] = stop

    def short_trade(
        self, strat_id, symbol, strength, sizing_type, tgt=np.nan, stop=np.nan
    ):
        """Add short Signal to Event and update strategy tracking.

        Args:
            strat_id ([type]): [description]
            symbol ([type]): [description]
            strength ([type]): [description]
            sizing_type ([type]): [description]
            tgt ([type]): [description]
            stop ([type]): [description]
        """
        sig_dir = "SHORT"
        signal = SignalEvent(
            strat_id, symbol, dt.datetime.now(), sig_dir, strength, sizing_type
        )
        self.events.put(signal)
        self.bought[symbol] = "SHORT"

        self.profit_tgt[symbol] = tgt
        self.stop_loss[symbol] = stop

    def exit_trade(self, strat_id, symbol):
        sig_dir = "EXIT"
        signal = SignalEvent(strat_id, symbol, dt.datetime.now(), sig_dir, 1.0, "exit")
        self.events.put(signal)
        self.bought[symbol] = "OUT"

        self.profit_tgt[symbol] = np.nan
        self.stop_loss[symbol] = np.nan
