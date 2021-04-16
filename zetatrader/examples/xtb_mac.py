import os
import logging
import pandas as pd
import numpy as np
import datetime as dt
# Import XTB engines
from zetatrader.event import SignalEvent
from zetatrader.indicator import moving_average_difference
from zetatrader.xtb.api import XRest
from zetatrader.xtb.price_data import PriceData
from zetatrader.xtb.book import XtbBook
from zetatrader.xtb.execution import XtbExecution
from zetatrader.portfolio.portfolio import Portfolio
from zetatrader.risk_manager import RiskManager
from zetatrader.trading.xtb_session import XtbSession

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

class MACrossover:
    """Base strategy for open close moving average crossover trading strategy.
    """
    def __init__(self, bars, events, connection, s_lb, l_lb, equity_risk
            , initial_stops=None):
        """[summary]

        Args:
            bars ([type]): [description]
            events ([type]): [description]
            lb ([type]): [description]
        """
        self.bars = bars
        self.events = events
        self.connection = connection
        self.initial_stops = initial_stops
        self.cmd_dict = {0 : 1, 1 : -1}
        self.symbol_list = self.bars.symbol_list
        self.holding_len = {x:-1 for x in self.symbol_list}
        self.profit_tgt = {x:0 for x in self.symbol_list}
        self.stop_loss = {x:0 for x in self.symbol_list}
        self.framesize = max(s_lb, l_lb) + 1
        self.last_candle_date = {
            x: dt.datetime(1990,1,1) for x in self.symbol_list
        }
        # Strategy parameters
        self.s_lb = s_lb
        self.l_lb = l_lb
        self.equity_risk = equity_risk
        # Strategy Risk Management 
        self.holdout_period = 60
        self.sd_window = self.l_lb
        self.tgt_mult = 4
        self.stop_mult = 2
        # Price and Indicator 
        self.price = self._construct_initial_indicators()
        self.bought = self._calculate_initial_bought()

        self._seed_indicator()

    def _calculate_initial_bought(self):
        """Populate current model current direction based on actual open 
        positions in our Books
        """
        bought = {}
        d = {x: 0 for x in self.symbol_list}
        open_trades = self.connection.get_open_positions()
        if not open_trades:
            return {x: 'OUT' for x in self.symbol_list}
        else:
            for lot in open_trades:
                symbol = lot['symbol']
                if lot['close_price'] > 0 and symbol in self.symbol_list:
                    d[symbol] += self.cmd_dict[lot['cmd']] * lot['volume']

        for symbol in self.symbol_list:
            curr_position = d[symbol]
            if curr_position != 0:
                if curr_position < 0:
                    bought[symbol] = 'SHORT'
                else:
                    bought[symbol] = 'LONG'
                if self.initial_stops is not None:
                    if symbol in self.initial_stops.index:
                        symbol_stop = self.initial_stops.loc[symbol, 'stop']
                        symbol_tgt = self.initial_stops.loc[symbol, 'target']
                        bars_since_trade = self.initial_stops.loc[symbol, 
                            'bars_since_trade']
                        if symbol_stop > 0:
                            self.stop_loss[symbol] = symbol_stop
                        if symbol_tgt > 0:
                            self.profit_tgt[symbol] = symbol_tgt
                        if bars_since_trade > 0:
                            self.holding_len[symbol] = bars_since_trade
            elif curr_position == 0:
                bought[symbol] = 'OUT'
            else:
                raise('current position is not a valid number')
        return bought
    
    def _construct_initial_indicators(self):
        price ={}
        for symbol in self.symbol_list:
            price[symbol] = pd.DataFrame(
                np.nan, index = [i for i in range(self.framesize)]
                , columns=['close_price']
            )
            price[symbol]['price_date'] = dt.datetime(1900, 1, 1)
        return price 

    def _seed_indicator(self):
        """Tries to prefill indicator with recent data up to the most recent
        t-1 data point. This amount of data populated depends on availability 
        of historical data. 
        """
        for symbol in self.symbol_list:
            candle = self.bars.get_latest_bars(
                symbol=symbol, n=self.framesize
            )
            if len(candle) > 1: 
                data_amt = len(candle) - 1
                self.price[symbol]['close_price'].iloc[-data_amt:] = (
                    candle.iloc[:-1]['close_price'])
                self.price[symbol]['price_date'].iloc[-data_amt:] = (
                    candle.iloc[:-1]['price_date'])

    def _long_trade(self, strat_id, symbol, strength, sizing_type, tgt, stop):
        """ADD LONG SIGNAL TO EVENT AND UPDATE STRATEGY TRACKING.

        Args:
            ticker ([type]): [description]
            strength ([type]): [description]
            sizing_type ([type]): [description]
        """
        sig_dir = 'LONG'
        signal = SignalEvent(
            strat_id, symbol, dt.datetime.now(), sig_dir, strength, sizing_type
        )
        self.events.put(signal)
        self.bought[symbol] = 'LONG'

        # SET TARGET AND STOP LOSS
        self.profit_tgt[symbol] = tgt
        self.stop_loss[symbol] = stop
        self.holding_len[symbol] = 0
    
    def _short_trade(self, strat_id, symbol, strength, sizing_type, tgt, stop):
        """Add short Signal to Event and update strategy tracking.

        Args:
            strat_id ([type]): [description]
            symbol ([type]): [description]
            strength ([type]): [description]
            sizing_type ([type]): [description]
            tgt ([type]): [description]
            stop ([type]): [description]
        """
        sig_dir = 'SHORT'
        signal = SignalEvent(
            strat_id, symbol, dt.datetime.now(), sig_dir
            , strength, sizing_type
        )
        self.events.put(signal)
        self.bought[symbol] = 'SHORT'

        self.profit_tgt[symbol] = tgt
        self.stop_loss[symbol] = stop
        self.holding_len[symbol] = 0
    
    def _exit_trade(self, strat_id, symbol):
        sig_dir = 'EXIT'
        signal = SignalEvent(
            strat_id, symbol, dt.datetime.now(), sig_dir, 1.0, 'exit'
        )
        self.events.put(signal)
        self.bought[symbol] = 'OUT'

        self.profit_tgt[symbol] = 0
        self.stop_loss[symbol] = 0
        self.holding_len[symbol] = -1 

    def calculate_signals(self, event):
        strategy_id = 1
        for symbol in self.symbol_list:
            # Update Price/Indicators
            curr_candle = self.bars.get_latest_bar(symbol)
            close_price = curr_candle.loc[0, 'close_price']
            current_bar_date = curr_candle.loc[0, 'price_date'] 
            last_candle_date = self.price[symbol]['price_date'].iloc[-1]
            if current_bar_date > last_candle_date:
                # Update Signal
                self.price[symbol] = self.price[symbol].shift(-1)
                self.price[symbol]['close_price'].iloc[-1] = close_price
                self.price[symbol]['close_price'].iloc[-1] = current_bar_date
                
                # Start Trading if Enough Historical Data 
                if sum(pd.isna(self.price[symbol]['close_price'])) == 0:
                    px = self.price[symbol]
                    sigma = px['close_price'].rolling(self.sd_window).std().iloc[-1]
                    px['ma_diff'] = moving_average_difference(px.close_price
                        , self.s_lb, self.l_lb)
                    trade_dir = 0
                    if px['ma_diff'].iloc[-1] > 0:
                        trade_dir = 1
                    elif px['ma_diff'].iloc[-1] < 0:
                        trade_dir = -1

                    if self.bought[symbol] == 'LONG':
                        self.holding_len[symbol] += 1
                        # CHECK FOR STOPPED OUT
                        if close_price<=self.stop_loss[symbol]:
                            # EXIT POS
                            print(f'LONG {symbol} - STOP OUT')
                            self._exit_trade(strat_id=strategy_id, symbol=symbol)
                            # CHECK FOR REVERSE TRADE
                            if trade_dir == -1:
                                self._short_trade(
                                    strat_id=strategy_id, symbol=symbol
                                    , strength={'percent_equity' : self.equity_risk
                                        , 'price_risk': sigma*self.stop_mult}
                                    , sizing_type='percent_equity_risk'
                                    , tgt=close_price - (sigma*self.tgt_mult)
                                    , stop=close_price + (sigma*self.stop_mult)
                                ) 
                        # CHECK FOR PROFIT TARGET REACH
                        elif (close_price>=self.profit_tgt[symbol] or 
                                self.holding_len[symbol]>=self.holdout_period):
                            if trade_dir == 1:
                                print(f'LONG {symbol}- ROLLOVER')
                                # ROLLOVER
                                # UPDATE TARGET/STOP
                                self.profit_tgt[symbol] = (
                                    close_price + (sigma*self.tgt_mult))
                                self.stop_loss[symbol] = (
                                    close_price - (sigma*self.stop_mult))
                                self.holding_len[symbol] = 0
                            elif trade_dir == -1:
                                print(f'LONG {symbol} - REVERSE')
                                # REVERSE    
                                self._exit_trade(strat_id=strategy_id, symbol=symbol)
                                self._short_trade(
                                    strat_id=strategy_id, symbol=symbol
                                    , strength={'percent_equity' : self.equity_risk
                                        , 'price_risk': sigma*self.stop_mult}
                                    , sizing_type='percent_equity_risk'
                                    , tgt=close_price - (sigma*self.tgt_mult)
                                    , stop=close_price + (sigma*self.stop_mult)
                                )
                            else:
                                self._exit_trade(strat_id=strategy_id, symbol=symbol)
                    elif self.bought[symbol] == 'SHORT':
                        self.holding_len[symbol] += 1
                        # CHECK FOR STOPPED OUT
                        if close_price>=self.stop_loss[symbol]: 
                            print(f'SHORT {symbol}- STOP OUT')
                            # STOPPED EXIT
                            self._exit_trade(strat_id=strategy_id, symbol=symbol)
                            if trade_dir == 1:
                                # REVERSE AND GO LONG
                                self._long_trade(
                                    strat_id=strategy_id, symbol=symbol
                                    , strength={'percent_equity' : self.equity_risk
                                        , 'price_risk': sigma*self.stop_mult}
                                    , sizing_type='percent_equity_risk'
                                    , tgt=close_price + (sigma*self.tgt_mult)
                                    , stop=close_price - (sigma*self.stop_mult)
                                )
                        elif (close_price<=self.profit_tgt[symbol] or 
                                self.holding_len[symbol]>=self.holdout_period):
                            if trade_dir==-1:
                                print(f'SHORT {symbol}- ROLLOVER')
                                # ROLLOVER
                                # UPDATE TARGET/STOP
                                self.profit_tgt[symbol] = (
                                    close_price - (sigma*self.tgt_mult))
                                self.stop_loss[symbol] = (
                                    close_price + (sigma*self.stop_mult))
                                self.holding_len[symbol] = 0
                            elif trade_dir == 1:
                                # REVERSE TRADE - GO LONG
                                print(f'SHORT {symbol} - REVERSE TO LONG')
                                self._exit_trade(strat_id=strategy_id, symbol=symbol)
                                self._long_trade(
                                    strat_id=strategy_id, symbol=symbol
                                    , strength={'percent_equity' : self.equity_risk
                                        , 'price_risk': sigma*self.stop_mult}
                                    , sizing_type='percent_equity_risk'
                                    , tgt=close_price + (sigma*self.tgt_mult)
                                    , stop=close_price - (sigma*self.stop_mult)
                                ) 
                            else:
                                self._exit_trade(strat_id=strategy_id, symbol=symbol) 
                    elif self.bought[symbol] == 'OUT':
                        if trade_dir == 1:
                            # GO LONG
                            print(f'GO LONG {symbol}')
                            self._long_trade(
                                strat_id=strategy_id, symbol=symbol
                                , strength={'percent_equity' : self.equity_risk
                                    , 'price_risk': sigma*self.stop_mult}
                                , sizing_type='percent_equity_risk'
                                , tgt=close_price + (sigma*self.tgt_mult)
                                , stop=close_price - (sigma*self.stop_mult)
                            ) 
                        elif trade_dir == -1:
                            # GO SHORT
                            print(f'GO SHORT {symbol}')
                            self._short_trade(
                                strat_id=strategy_id, symbol=symbol
                                , strength={'percent_equity' : self.equity_risk
                                    , 'price_risk': sigma*self.stop_mult}
                                , sizing_type='percent_equity_risk'
                                , tgt=close_price - (sigma*self.tgt_mult)
                                , stop=close_price + (sigma*self.stop_mult)
                            )
            else:
                # No New Info for this Symbol
                pass

    
if __name__ == '__main__':
    current_stops = pd.read_csv('initial_stops.csv', index_col='symbol')
    symbol_list = ['ZINC', 'OIL']
    client = XRest(os.environ.get('XTB_DEMO_USER')
        , os.environ.get('XTB_DEMO_PW'), islive=False)

    trading_sess = XtbSession(
        symbol_list = symbol_list,
        heartbeat = 60,
        price_handler = PriceData,
        execution_handler = XtbExecution,
        portfolio=Portfolio,
        strategy=MACrossover,
        book=XtbBook,
        money_management=RiskManager,
        connection=client,
        other_parameters={
            'price_handler_param': {
                'barsize' : '1MIN'
            },
            'strategy_param' : {
                's_lb': 10, 'l_lb': 60, 'equity_risk': 0.005, 
                'initial_positions' : current_stops
            }
        } 
    )