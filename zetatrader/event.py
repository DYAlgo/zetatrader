#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# event.py
# Darren


class Event(object):
    """
    Event is base class providing an interface for all subsequent
    (inherited) events, that will trigger further events in the
    trading infrastructure.
    """

    pass


class MarketEvent(Event):
    """
    Handles the event of receiving a new market update with
    corresponding bars.
    """

    def __init__(self):
        """
        Initialises the MarketEvent.
        """
        self.type = "MARKET"


class CloseEvent(Event):
    """
    Handles the event of receiving a non-trading day or holiday
    update.
    """

    def __init__(self):
        """
        Initialises the CloseEvent.
        """
        self.type = "CLOSE"


class SignalEvent(Event):
    """
    Handles the event of sending a Signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    """

    def __init__(
        self,
        strategy_id,
        symbol,
        datetime,
        signal_type,
        strength,
        money_management_key=0,
    ):
        """Initializes the SignalEvent.

        Arguments:
            strategy_id {int,str} -- The unique ID of the strategy used.
            symbol {int,str} -- The ticker symbol
            datetime {datetime} -- Timestamp at which the signal was generated
            signal_type {str} -- 'LONG' or 'SHORT'.
            strength {float} -- An adjustment factor "suggestion" used to scale
                quantity at the portfolio level. Useful for pairs strategies.

        Keyword Arguments:
            money_management_key {int} -- Unique key used by money_management
                object to use specific position sizing method (default: {1})
        """
        self.strategy_id = strategy_id
        self.type = "SIGNAL"
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength
        self.money_management_key = money_management_key


class OrderEvent(Event):
    """
    Handles the event of sending an Order to an execution system.
    The order contains a symbol (e.g. GOOG), a type (market or limit),
    quantity and a direction.
    """

    def __init__(self, symbol, order_type, quantity, direction, lot_id=0, isexit=False):
        """
        Initialises the order type, setting whether it is
        a Market order ('MKT') or Limit order ('LMT'), has
        a quantity (integral) and its direction ('BUY' or
        'SELL').

        TODO: Must handle error checking here to obtain
        rational orders (i.e. no negative quantities etc).

        Parameters:
        symbol - The instrument to trade.
        order_type - 'MKT' or 'LIMIT' for Market or Limit.
        quantity - Non-negative integer for quantity.
        direction - 'BUY' or 'SELL' for long or short.
        """
        self.type = "ORDER"
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction
        self.lot_id = lot_id
        self.isexit = isexit

    def print_order(self):
        """
        Outputs the values within the Order.
        """
        print(
            "Order: Symbol=%s, Type=%s, Quantity=%s, Direction=%s"
            % (self.symbol, self.order_type, self.quantity, self.direction)
        )


class FillEvent(Event):
    """
    Encapsulates the notion of a Filled Order, as returned
    from a brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores
    the commission of the trade from the brokerage.

    TODO: Currently does not support filling positions at
    different prices. This will be simulated by averaging
    the cost.
    """

    def __init__(
        self,
        timeindex,
        symbol,
        exchange,
        quantity,
        direction,
        fill_cost,
        commission=0,
        lot_id=0,
    ):
        """
        Initialises the FillEvent object. Sets the symbol, exchange,
        quantity, direction, cost of fill and an optional
        commission.

        If commission is not provided, the Fill object will
        calculate it based on the trade size and Interactive
        Brokers fees.

        Parameters:
        timeindex - The bar-resolution when the order was filled.
        symbol - The instrument which was filled.
        exchange - The exchange where the order was filled.
        quantity - The filled quantity.
        direction - The direction of fill ('BUY' or 'SELL')
        fill_cost - The holdings value in dollars. (Non-negative)
        commission - An optional commission sent from IB.
        """
        self.type = "FILL"
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        self.lot_id = lot_id

        # Calculate commission
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        """
        Calculates the fees of trading based on an Interactive
        Brokers fee structure for API, in USD.

        This does not include exchange or ECN fees.

        Based on "US API Directed Orders":
        https://www.interactivebrokers.com/en/index.php?f=commission&p=stocks2
        """
        full_cost = 5.00
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else:  # Greater than 500
            full_cost = max(1.3, 0.008 * self.quantity)
        return full_cost
