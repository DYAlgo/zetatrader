
from os import curdir
from zetatrader.event import OrderEvent
from zetatrader.portfolio.base import AbstractPortfolio

class SimulatedPortfolio(AbstractPortfolio):
    """Simulates a portfolio of equities and holds position sizing
    algorithms tailored for Equities asset classes.
    """
    def __init__(self, bars, events, performance, initial_capital):
        """Initializes SimulatedPortfolio

        Args:
            events (Obj): EventQueue 
            bars (Obj): Price Handler Object
            initial_capital (int): Starting Capital
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.total_equity = initial_capital
        self.performance = performance
        # Position Trackers
        self.current_positions = self.construct_current_position()
        self.current_holdings = self.construct_current_holdings()
        self.all_positions = self.construct_all_positions()
        self.all_holdings = self.construct_all_holdings()
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
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all symbols.
        """
        # Add code to get position from broker if trading session is live
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['cash'] = self.total_equity
        d['commission'] = 0.0
        d['total'] = self.total_equity
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
        d['cash'] = self.total_equity
        d['commission'] = 0.0
        d['total'] = self.total_equity
        return [d]


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
                dh[s] = market_value
                self.current_holdings[s] = market_value
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
        self.equity = dh['total']
        self.all_holdings.append(dh)

    
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

        # Use fill.fill_cost which returns next opens price. 
        # Update holdings list with new quantities
        fill_cost = fill.fill_cost
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        # Take cost amount out from total and add new mv on next bar
        self.current_holdings['total'] -=  fill.commission 
        self.total_equity = self.current_holdings['total']     

        print(
            '%s %s Order filled - date:%s price:%s size:%s units' %(
                    fill.direction, fill.symbol, self.bars.get_datetime()
                    , fill_cost, fill.quantity
                )
            )

    
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
        qty = signal.strength
        
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
        equity = self.total_equity
        portfolio_risk = equity * signal.strength['percent_equity']
        target_qty = portfolio_risk/signal.strength['price_risk']

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
                quantity=target_qty,
                direction='SELL',
                isexit=False
            ) 
        else:
            raise 'Incorrect combination of direction and quantity' 