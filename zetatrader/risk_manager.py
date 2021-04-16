#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# money_management.py
# Darren Jun Yi Yeap 03/07/2020
from zetatrader.event import OrderEvent

class RiskManager:
    """Encapsules the interaction between a Signals and Risk Management.
    This class holds functions for position sizing and risk management. 
    """
    def __init__(self, bars, book):
        self.book = book
        self.bars = bars 
        self.position_sizing_dict = {
            'exit' : self.exit_order, 
            'naive_order' : self.naive_order,
            'percent_equity_risk' : self.percent_equity_risk_order 
        }
        
    # ========================================= #
    # Money Management algo
    # ========================================= #
    def resized_order(self, event):
        """Returns a Order Event generated from a money management
        method that specified through the money management dictionary
        
        Arguments:
            event {obj} -- Signal Event object
        """
        identifier = event.money_management_key
        try:
            order_event = self.position_sizing_dict[identifier](event)
            return order_event
        except KeyError as e:
            print("%s \n"%e +
                "The money management method specified in Signal Event "+
                "was not found.")
            raise 

    # ========================================= #
    # Positiong Sizing Type
    # ========================================= #
    def exit_position(self, signal):
        order_type = 'MKT'
        direction = signal.signal_type
        cur_quantity = self.book.current_positions[signal.symbol]

        if signal.signal_type  == 'EXIT' and cur_quantity != 0:
            # Close Out Position Regarless Direction
            self.book.close_position(signal.symbol)
        elif signal.signal_type  == 'EXIT' and cur_quantity == 0:
            print(f'No {signal.symbol} position to exit')
        else:
            raise('Incorrect combination of Signal Type and current quantitiy.')
    
    def naive_order(self, signal):
        symbol = signal.symbol
        direction = signal.signal_type
        cur_quantity = self.book.current_positions[signal.symbol]
        
        if direction == 'LONG' and cur_quantity >= 0:
            # Long Order
            self.book.add_position(symbol, signal.strength, 'BUY')
        elif direction == ' SHORT' and cur_quantity <=0:
            # Short Order
            self.book.add_position(symbol, signal.strength, 'SELL')
        else:
            raise('Incorrect combination of direction and quantity')

    def percent_equity_risk_order(self, signal):
        """Create order size such that your exiting at your stop loss
        will result in approximately x% of your equity. The function
        for computing the order size is 
            = (equity*percent_risk)/(num_ticks * tick_value)

        Args:
            signal (SignalEvent): [description]
        """
        symbol = signal.symbol
        direction = signal.signal_type
        cur_quantity = self.book.current_positions[signal.symbol]
        equity = self.book.equity
        tick_value = self.book.symbol_info['']
        tick_size = self.book.symbol_info['']
        total_ticks = signal.strength['price_risk']/tick_size

        portfolio_risk = equity * signal.strength['percent_equity']
        contract_risk = abs(total_ticks) * tick_value
        target_qty = portfolio_risk/contract_risk

        if direction == 'LONG' and cur_quantity >= 0:
            # Add to LONG POSITION
            self.book.add_position(symbol, target_qty, 'BUY')
        elif direction == 'SHORT' and cur_quantity <= 0:
            # Add to SHORT POSITION
            self.book.add_position(symbol, target_qty, 'SELL') 
        else:
            raise('Incorrect combination of direction and quantity')
