from math import floor
from zetatrader.event import OrderEvent
from zetatrader.portfolio.simulated_portfolio import AbstractPortfolio

class FuturesPortfolio(AbstractPortfolio):
    """A simulation portfolio for futures and CFDs.
    """
    def __init__(self, bars, events, performance, initial_capital, symbol_info):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.performance = performance 
        self.total_equity = initial_capital 
        self.symbol_info = symbol_info
        # Portfolio Tracker
        self.current_positions = self.construct_current_position()
        self.current_holdings = self.construct_current_holdings()
        # self.current_notionals = self.construct_current_notionals()
        self.current_margins = self.construct_current_margins()
        self.all_positions = self.construct_all_positions()
        self.all_holdings = self.construct_all_holdings()
        # self.all_notionals = self.construct_all_notionals()
        self.all_margins = self.construct_all_margins()
        # Position Sizing Tracker
        self.position_sizing_dict = {
            'exit' : self.exit_order, 
            'naive_order' : self.naive_order,
            'percent_equity_risk' : self.percent_equity_risk_order 
        }

    # ==================================================== #
    # Portfolio Constructors
    # ==================================================== #
    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the notional 
        value of each asset in our portfolio.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['cash'] = self.total_equity
        d['commission'] = 0.0
        d['total'] = self.total_equity
        d['total_notional'] = 0
        return d

    def construct_current_position(self):
        """Constructs a dictionary of tickers and the position we have for each
        symbol.

        Returns:
            [Dict]: Symbol (Key): Number of units we own
        """
        d = dict( 
            (k,v) for k, v in [(s, 0) for s in self.symbol_list] 
        )
        return d 

    def construct_current_margins(self):
        """Constructs a dictionary to track the net exposure of our positions 
        in terms of margin requirements of our positions. This will be similar
        to the direction times current margin. 
        """
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['commission'] = 0.0
        d['cash'] = self.total_equity
        d['total'] = self.total_equity
        return d
    
    def construct_current_notional(self):
        """Constructs a dictionary to track the notional value of our positions. 
        """
        d = dict( 
            (k,v) for k, v in [(s, 0) for s in self.symbol_list] 
        )
        return d 

    
    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date
        to determine when the time index will begin.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        d['datetime'] = self.bars.start_dt
        return [d]
    
    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date
        to determine when the time index will begin.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['datetime'] = self.bars.start_dt
        # d['cash'] = self.total_equity
        d['commission'] = 0.0
        d['cash'] = self.total_equity
        d['total'] = self.total_equity
        d['total_notional'] = 0
        return [d]

    def construct_all_margins(self):
        """
        Constructs a list to store current margins across backtest.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['datetime'] = self.bars.start_dt
        d['commission'] = 0.0
        d['total'] = self.total_equity
        return [d]

    def construct_all_notional(self):
        """
        Constructs a list to store the notional value across backtest period. 
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        return [d]

    # ==================================================== #
    # Update Portfolio Index, Value, and Position
    # ==================================================== #
    def update_timeindex(self, event):
        """Updates the current position, margin, exposure, and notional values
        of assets held in portfolio as of latest price. We are going to assume 
        that we are trading these futures/CFD in the same currency as these
        assets. 
        """
        latest_datetime = self.bars.get_latest_bar_datetime()

        # Update Positions
        dp = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dp['datetime'] = latest_datetime
        for s in self.symbol_list:
            dp[s] = self.current_positions[s] 
        # Append the current positions
        self.all_positions.append(self.current_positions[s])

        # Update Margins 
        dm = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dm['cash'] = self.current_margins['cash']
        dm['total'] = self.current_margins['cash']
        dm['commission'] = self.current_margins['commission']
        dm['datetime'] = latest_datetime

        # Update Holdings
        dh = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dh['datetime'] = latest_datetime
        # dh['cash'] = self.current_margins['cash']
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']
        dh['total_notional'] = 0

        # Update Notional
        dn = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dn['datetime'] = latest_datetime
        dn['total'] = self.current_margins['cash']

        for symbol in self.symbol_list:
            volume = self.current_positions[symbol]
            last_price = self.bars.get_latest_bar_value(symbol, "close_price")
            contract_size = self.symbol_info[symbol]['contract size']
            margin_requirements = 1/self.symbol_info[symbol]['leverage']
            # exposure = 1 if volume > 0 else (-1 if volume < 0 else 0)
            notional_value = contract_size * last_price * volume
            new_margin_req = abs(notional_value * margin_requirements)

            # Add to margin
            dm[symbol] = new_margin_req
            dm['total'] += new_margin_req

            # Add to Holdings
            # Change in Total should be current notional - previous notional
            dh[symbol] = notional_value
            dh['total'] += notional_value
            dh['total_notional'] += notional_value

        self.total_equity = dh['total']
        self.current_holdings = dh
        self.current_margins = dm
        # Save a copy of holdings and margins for performance measurement
        self.all_holdings.append(dh.copy())
        self.all_margins.append(dm.copy())
        
    # ========================= #
    # SIGNAL HANDLING 
    # ========================= #
    def update_signal(self, event):
        """Acts on the SignalEvent and utilize money_management
        and risk management 
        
        Arguments:
            event {obj} -- SignalEvent object 
        """
        if event.type == 'SIGNAL':
            order = self.resize_order(event)
            self.events.put(order)

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


    # ======================
    # FILL/POSITION HANDLING
    # ======================
    def update_fill(self, event):
        """
        Takes a Fill Event to update our portfolio position and holdings
        plus recording this filled in our performance. 
        
        Arguments:
            event {obj} -- Fill Event
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_margins_from_fill(event)
            self.update_holdings_from_fill(event)
            self.performance.update_trade_log(event)
    
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

        # Update holdings list with new quantities
        symbol = fill.symbol
        contract_size = self.symbol_info[symbol]['contract size']
        fill_cost = fill.fill_cost
        cost = fill_dir * fill_cost * fill.quantity * contract_size
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        # Take cost amount out from total and add new mv on next bar
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= fill.commission
        self.current_holdings['total_notional'] -= cost

        print(f'{fill.direction} {fill.quantity} units of {fill.symbol}'
            + f' Order Filled on {self.bars.get_datetime()} at {fill_cost}')

    def update_margins_from_fill(self, fill):
        """Updates the margins our portfolio is current holding based
        on newly updated current positions.

        Args:
            fill ([type]): [description]
        """
        symbol = fill.symbol
        curr_position = self.current_positions[symbol]
        contract_size = self.symbol_info[symbol]['contract size']
        prior_margin_req = self.current_margins[symbol]
        margin_requirements = 1/self.symbol_info[symbol]['leverage']
        new_margin_req = abs(curr_position * contract_size * 
            margin_requirements * fill.fill_cost)

        self.current_margins[symbol] = new_margin_req
        self.current_margins['cash'] -=  (new_margin_req - 
            prior_margin_req + fill.commission) 
        self.current_margins['commission'] -= fill.commission 
        self.current_margins['total'] -=  fill.commission
        self.total_equity = self.current_margins['total']
    
    # ======================
    # SAVE PORTFOLIO
    # PERFORMANCE
    # ======================
    def save_portfolio_performance(self):
        """Save all portfolio level performance statistics through 
        performance object. These are:
        1. equity curve record 
        2. trade log. 
        """
        self.performance.save_equity_curve(self.all_holdings)
        self.performance.save_trade_log()


    # ==================================================== #
    # POSITION SIZERS
    # ==================================================== #
    def round_down(self, volume, lot_size):
        return floor(volume*(1/lot_size))/(1/lot_size)
    
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