#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# execution.py
# @author: Darren

from abc import ABCMeta, abstractmethod

from zetatrader.event import FillEvent


class ExecutionHandler(object):
    """
    The ExecutionHandler abstract class handles the interaction
    between a set of order objects generated by a Portfolio and
    the ultimate set of Fill objects that actually occur in the
    market.

    The handlers can be used to subclass simulated brokerages
    or live brokerages, with identical interfaces. This allows
    strategies to be backtested in a very similar manner to the
    live trading engine.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        """
        Takes an Order event and executes it, producing
        a Fill event that gets placed onto the Events queue.

        Parameters:
        event - Contains an Event object with order information.
        """
        raise NotImplementedError("Should implement execute_order()")


class SimulatedExecution(ExecutionHandler):
    """
    The simulated execution handler simply converts all order
    objects into their equivalent fill objects automatically
    without latency or fill-ratio issues. However, it factors in
    slippage in the form of using next bars open price as the
    filled price. This allows for more accurate representation
    of slippage especially for low frequency strategies such
    as daily, weekly, or monthly bars.

    This is an alternative "first go" test of any strategy,
    before implementation with a more sophisticated execution
    handler.
    """

    def __init__(self, events, bars=None, on_open=True, commission=0.0):
        """
        Initialises the handler, setting the event queues
        up internally.

        Parameters:
        events - The Queue of Event objects.
        bars - The datahandler object
        commission - Commissions per trade
        """
        self.events = events
        self.bars = bars
        self.on_open = on_open
        self.commission = commission

        if bars is None:
            print("Data Handler not inserted into Execution Handler")

    def __str__(self):
        """
        Prints the name of this strategy
        """
        return "NextOpenSimulatedExecution"

    def execute_order(self, event):
        """
        Converts Order objects into Fill objects without any latency
        or fill ratio problems. Calls a function within the
        data handler for the next open price and insert that as the
        fill_cost. A fill event contains: fill time, symbol, exchange
        name, quantity, direction, fill price/cost, commission.

        Parameters:
        event - Contains an Event object with order information.
        """
        if event.type == "ORDER":
            fill_cost = None
            timeindex = self.bars.get_latest_bar_datetime(event.symbol)

            if self.on_open:
                # Use next open as fill-price
                try:
                    fill_cost = self.bars.get_next_open_price(event.symbol)
                except:
                    print("%s Order Not Filled" % event.symbol)
                else:
                    fill_event = FillEvent(
                        timeindex,
                        event.symbol,
                        "BACKTEST EXCHANGE",
                        abs(event.quantity),
                        event.direction,
                        fill_cost,
                        commission=self.commission,
                    )
                    self.events.put(fill_event)
            else:
                # Use current close price as fill-price
                fill_cost = self.bars.get_latest_bar_value(event.symbol, "close_price")
                fill_event = FillEvent(
                    timeindex,
                    event.symbol,
                    "BACKTEST EXCHANGE",
                    abs(event.quantity),
                    event.direction,
                    fill_cost,
                    commission=self.commission,
                )
                self.events.put(fill_event)
