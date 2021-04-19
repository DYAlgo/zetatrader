import time 
import datetime as dt
from math import floor
from zetatrader.event import OrderEvent
from zetatrader.portfolio.simulated_portfolio import AbstractPortfolio

def fromtimestamp(x):
    return dt.datetime.fromtimestamp(x)

class XtbPortfolio(AbstractPortfolio):
    """This class provides interface for interacting with our holdings
    at XTB and order management of new and existing positions.
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
        self.total_equity = self.get_equity()
        self.balance = self.get_balance()
        self.total_margin = self.get_margin()
        self.all_holdings = self.construct_all_holdings()
        self.all_positions = self.construct_all_positions()
        self.all_margins = self.construct_all_margins()
        # Get Current Portfolio Position
        self.current_lots = None
        self.current_positions = None
        self.current_holdings = None
        self.current_margins = None
        self.current_notional = None
        self.net_exposure = None # TODO: Store margins with +- signs.

        self.position_sizing_dict = {
            'exit' : self.exit_order, 
            'naive_order' : self.naive_order,
            'percent_equity_risk' : self.percent_equity_risk_order 
        }
    

    # ==================================================== #
    # HELPER FUNCTION
    # ==================================================== #
    def round_down(self, volume, lot_size):
        return floor(volume*(1/lot_size))/(1/lot_size)


    # ==================================================== #
    # ACCOUNT INFO CONSTRUCTOR
    # ==================================================== # 
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
    # PORTFOLIO CONSTRUCTOR
    # ==================================================== # 
    def construct_symbol_info(self):
        d = {}
        for symbol in self.symbol_list:
            d[symbol] = self.connection.get_symbol_info(symbol, False)
            d[symbol]['tick value'] = d[symbol]['tickValue'] 
            d[symbol]['tick size'] = d[symbol]['tickSize'] 
            d[symbol]['contract size'] = d[symbol]['contractSize']
            time.sleep(0.2)
        return d
    
    def construct_current_book(self):
        """Constructs the initial position, margins and holdings values.
        """
        # Get most up-to-date open lots
        self.current_lots = self.get_current_lots()

        # Update Current Portfolio using current lots
        self.current_positions = self.construct_current_position()
        self.current_margins = self.construct_current_margins()
        self.current_holdings = self.construct_current_holdings()
        print('Initial Portfolio Constructed') 

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
    
    def construct_current_position(self):
        """
        Contructs a dictionary for total volume of each symbol.  
        """
        d = {}
        d['datetime'] = dt.datetime.now()
        for i in self.symbol_list:
            d[i] = 0
            all_lot_id = list(self.current_lots[i].keys())
            if all_lot_id:
                for l in all_lot_id:
                    lot = self.current_lots[i][l]
                    d[i] += lot['direction'] * lot['volume']
        return d
    
    def construct_current_holdings(self):
        """Updates current holdings with Notional Values of Each symbol.
        """
        d = {i: 0 for i in self.symbol_list}
        d['datetime'] = dt.datetime.now()
        for symbol in self.symbol_list:
            # Notional is just the margin * leverage on that asset class
            leverage = self.symbol_info[symbol]['leverage']
            current_margin = self.current_margins[symbol]
            notional = current_margin * leverage
            d[symbol] = notional
        d['total'] = self.total_equity
        d['cash'] = self.total_equity - self.total_margin
        return d

    def construct_current_margins(self):
        total_margin = 0
        d = {i: 0 for i in self.symbol_list}
        d['datetime'] = dt.datetime.now()
        for symbol in self.symbol_list:
            volume = self.current_positions[symbol]
            d[symbol] = self.connection.get_margin_requirement(symbol, volume)
            time.sleep(0.2) # To prevent flooding API
            total_margin += d[symbol]
        d['total'] = self.total_equity
        d['cash'] = self.total_equity -total_margin
        return d

    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date
        to determine when the time index will begin.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        d['datetime'] = dt.datetime.now()
        return [d]

    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date
        to determine when the time index will begin.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['datetime'] = dt.datetime.now()
        # d['cash'] = self.total_equity
        d['commission'] = 0.0
        d['cash'] = self.total_equity
        d['total'] = self.total_equity
        d['total_notional'] = 0
        return [d]
    
    def construct_all_margins(self):
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['datetime'] = dt.datetime.now()
        # d['cash'] = self.total_equity
        d['commission'] = 0.0
        d['cash'] = self.total_equity
        d['total'] = self.total_equity
        d['total_notional'] = 0
        return [d]


    # ==================================================== #
    # Update PORTFOLIO
    # ==================================================== # 
    def update_timeindex(self, event):
        """Updates Snapshot of position value and information
        """
        # Update Account Value
        account_info = self.connection.get_account_info()
        self.total_equity = account_info['equity'] 
        self.balance = account_info['balance']
        self.total_margin = account_info['margin']

        # Update Current lots, then position, then holdings. 
        self.current_lots = self.get_current_lots()
        self.current_positions = self.construct_current_position()
        self.current_margins = self.construct_current_margins()
        self.current_holdings = self.construct_current_holdings()

        # Store Previous Margin and Holdings Info
        self.all_positions.append(self.current_positions.copy())
        self.all_holdings.append(self.current_holdings.copy())
        self.all_margins.append(self.current_margins.copy())

    # ==================================================== #
    # SIGNAL HANDLING
    # ==================================================== # 
    def update_signal(self, event):
        """Acts on the SignalEvent and utilize money_management
        and risk management 
        
        Arguments:
            event {obj} -- SignalEvent object 
        """
        if event.type == 'SIGNAL':
            order = self.resize_order(event)
            # Let Portfolio Inventory (lot) decide execution type 
            self.execute_portfolio_order(order)

    def resize_order(self, signal):
        """[summary]

        Args:
            signal ([type]): [description]
        """
        ps_name = signal.money_management_key
        try:
            order = self.position_sizing_dict[ps_name](signal)
            return order
        except KeyError as e:
            raise (f"{ps_name} Position Sizer method not found") 


    # ==================================================== #
    # PORTFOLIO INVENTORY HANDLING
    # ==================================================== # 
    def execute_portfolio_order(self, event):
        """Modifies order based on current invetory of portfolio. If we have
        an order to SELL 4 of the 5 units of Asset A, the function here
        will produce N orders to SELL those 4 units.
        """
        if event.type == 'ORDER':
            symbol = event.symbol
            if event.isexit == True:
                # Loop through all lots and exit it
                all_lot_id = list(self.current_lots[symbol].keys())
                for l in all_lot_id:
                    order_dir = None
                    lot_dir = self.current_lots[symbol][l]['direction']
                    if lot_dir == 1:
                        order_dir = 'SELL'
                    elif lot_dir == -1:
                        order_dir = 'BUY'
                    else:
                        raise f'Lot direction is neither 1 or -1.'
                    lot_size = self.current_lots[symbol][l]['volume']
                    order = OrderEvent(
                        symbol, 'MKT', lot_size, order_dir, lot_id=l
                        , isexit=True 
                    )
                    self.events.put(order)
                    self.current_positions[symbol] -= lot_dir * lot_size
            elif event.direction == 'BUY':
                if self.current_positions[symbol] < 0:
                    units = event.quantity
                    # Sell out current position then go long net remaining position
                    all_lot_id = list(self.current_lots[symbol].keys())
                    for l in all_lot_id:
                        if units > 0:
                            # Keep liquidating
                            lot_size = self.current_lots[symbol][l]['volume']
                            lot_dir = self.current_lots[symbol][l]['direction']
                            if lot_size <= units:
                                # Exit Whole Unit
                                order = OrderEvent(
                                    symbol, 'MKT', lot_size, 'BUY', l, 
                                    isexit=True
                                )
                                self.events.put(order)
                                self.current_positions[symbol] -= lot_dir * lot_size
                                units = units - lot_size
                            elif lot_size > units:
                                # Partial Exit
                                order = OrderEvent(
                                    symbol, 'MKT', units, 'BUY', lot_id=l, 
                                    isexit=True
                                )
                                self.events.put(order)
                                self.current_positions[symbol] -= lot_dir * units
                                units = 0
                                break
                else:
                    self.events.put(event)
            elif event.direction == 'SELL':
                if self.current_positions[symbol] > 0:
                    units = event.quantity
                    # Sell out current position then go long net remaining position
                    all_lot_id = list(self.current_lots[symbol].keys())
                    for l in all_lot_id:
                        if units > 0:
                            # Keep liquidating
                            lot_size = self.current_lots[symbol][l]['volume']
                            lot_dir = self.current_lots[symbol][l]['direction']
                            if lot_size <= units:
                                # Exit Whole Unit
                                order = OrderEvent(
                                    symbol, 'MKT', lot_size, 'SELL', l, 
                                    isexit=True
                                )
                                self.events.put(order)
                                self.current_positions[symbol] -= lot_dir * lot_size
                                units = units - lot_size
                            elif lot_size > units:
                                # Partial Exit
                                order = OrderEvent(
                                    symbol, 'MKT', units, 'SELL', lot_id=l, 
                                    isexit=True
                                )
                                self.events.put(order)
                                self.current_positions[symbol] -= lot_dir * units
                                units = 0
                                break
                else: 
                    self.events.put(event)


    # ==================================================== #
    # POSITION SIZERS
    # ==================================================== #
    def exit_order(self, signal):
        order_type = 'MKT'
        direction = signal.signal_type
        cur_quantity = self.current_positions[signal.symbol]

        if signal.signal_type  == 'EXIT' and cur_quantity < 0:
            return OrderEvent(
                symbol = signal.symbol,
                order_type='MKT',
                quantity=abs(cur_quantity),
                direction='BUY',
                isexit=True
            )
        elif signal.signal_type  == 'EXIT' and cur_quantity > 0:
            return OrderEvent(
                symbol = signal.symbol,
                order_type='MKT',
                quantity=abs(cur_quantity),
                direction='SELL',
                isexit=True
            )
        elif signal.signal_type  == 'EXIT' and cur_quantity == 0:
            print(f'No {signal.symbol} position to exit')
        else:
            raise f'Incorrect Signal combination given'

    def naive_order(self, signal):
        symbol = signal.symbol
        direction = signal.signal_type
        lot_size = self.symbol_info[symbol]['lotMin']
        qty = signal.strength
        qty = self.round_down(qty, lot_size=lot_size)
        
        if direction == 'LONG':
            # Long Order
            return OrderEvent(
                symbol = signal.symbol,
                order_type='MKT',
                quantity=abs(qty),
                direction='BUY',
                isexit=False
            )            
        elif direction == ' SHORT':
            return OrderEvent(
                symbol = signal.symbol,
                order_type='MKT',
                quantity=abs(qty),
                direction='SELL',
                isexit=False
            )
        else:
            raise('Incorrect combination of for Naive Order')

    def percent_equity_risk_order(self, signal):
        """Create order size such that your exiting at your stop loss
        will result in approximately x% of your equity. The function
        for computing the order size is 
            = (equity*percent_risk)/(dollar risk per equity)

        Args:
            signal (SignalEvent): [description]
        """
        symbol = signal.symbol
        direction = signal.signal_type
        tick_size = self.symbol_info[symbol]['tick size']
        tick_value = self.symbol_info[symbol]['contract size'] * tick_size
        total_ticks = signal.strength['price_risk']/tick_size
        portfolio_risk = self.total_equity * signal.strength['percent_equity']
        lot_size = self.symbol_info[symbol]['lotMin']
        contract_risk = abs(total_ticks) * tick_value
        target_qty = portfolio_risk/contract_risk
        target_qty = self.round_down(target_qty, lot_size=lot_size)

        if direction == 'LONG':
            return OrderEvent(
                symbol = signal.symbol,
                order_type='MKT',
                quantity=abs(target_qty),
                direction='BUY',
                isexit=False
            ) 
        elif direction == 'SHORT':
            return OrderEvent(
                symbol = signal.symbol,
                order_type='MKT',
                quantity=abs(target_qty),
                direction='SELL',
                isexit=False
            ) 
        else:
            raise 'Incorrect combination of direction and quantity' 