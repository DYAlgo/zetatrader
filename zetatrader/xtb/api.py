import os
import pandas as pd
import datetime as dt
from dateutil import tz
from pytz import timezone

# Import from own package
from zetatrader.xtb.xAPIConnector import APIClient
from zetatrader.xtb.xAPIConnector import DEFAULT_XAPI_ADDRESS

# DEFAULT_XAPI_PORT = 5112 # Use 5124 for DEMO
# DEFUALT_XAPI_STREAMING_PORT = 5113 # Use 5125 for DEMO
def fromtimestamp(x):
    return dt.datetime.fromtimestamp(x, )

class XRest(APIClient):
    """[summary]
    """
    def __init__(self, user=None, pw=None, sess_name='Test', islive=False
            , address=DEFAULT_XAPI_ADDRESS):
        port_num = 5124
        if islive == True:
            port_num = 5112

        super().__init__(
            address = address
            , port = port_num
            , encrypt = True 
        )
        self.sess_name = sess_name
        self._user = user
        self._pw = pw
        self.login(self._user, self._pw)
        
    def login(self, user=None, pw=None):
        if (user != None) and (pw != None):
            login_response = self.commandExecute(
                commandName='login',
                arguments={
                    'userId': user
                    , 'password': pw
                    , 'appName': self.sess_name
                }
            )
            
            if login_response.get('status') == True:
                print(login_response)
            else:
                print(
                    f'Login Error. Error code: {login_response["errorCode"]}'
                )
                raise Exception(
                    f'Login Error: {login_response["errorCode"]}'
                )
        # TODO: Add logger to function

    # ============================ #
    # HELPER FUNCTION
    # ============================ #
    def _print(self, message):
        """Print error message when status is false.

        Args:
            message (dict): Info returned by socket
        """
        print(f'Request Error {message.get("errorCode")}')
        raise Exception(message.get("errorDescr"))

    # ====================== #
    # PLATFORM INFO 
    # ====================== #
    def get_server_time(self):
        """Return Server Time in CET/CEST time zone. 

        Returns:
            [type]: [description]
        """
        server_time = self.commandExecute(
                commandName = 'getServerTime'
        )
        if server_time.get('status') == True:
            time_now = server_time.get('returnData')['time']/1000
            london_time = timezone('Europe/London').localize(fromtimestamp(time_now))
            ces_time = london_time.astimezone(timezone('Europe/Berlin'))
            return ces_time.replace(tzinfo=None)
        else:
            self._print(server_time)

    def ping(self):
        """Returns ping to server. 

        Returns:
            [type]: [description]
        """
        ping_info = self.commandExecute(commandName='ping')
        if ping_info.get('status') == True:
            return True
        else:
            self._print(ping_info)
            return False

    def get_account_info(self):
        acc_info = self.commandExecute(
                commandName = 'getMarginLevel'
        )
        if acc_info.get('status') == True:
            return acc_info.get('returnData')
        else:
            self._print(acc_info)

    # ====================== #
    # SYMBOL INFO 
    # ====================== #
    def get_all_symbols(self, symbol_as_index=True):
        """Returns symbol information for all symbols on XTB.
        """
        symbol_info = self.commandExecute(commandName='getAllSymbols')
        
        if symbol_info.get('status') == True:
            df = pd.json_normalize(symbol_info.get('returnData'))
            if symbol_as_index:
                df.set_index('symbol', inplace=True)
            return df
        else:
            self._print(symbol_info)
            return None

    def get_symbol_info(self, ticker, as_df=True):
        """Returns information of a given symbol
        """
        symbol_info = self.commandExecute(
            commandName='getSymbol', 
            arguments={
                "symbol": ticker
            }
        )

        if symbol_info.get('status') == True:
            if as_df:
                return pd.json_normalize(symbol_info.get('returnData'))
            else:
                return symbol_info.get('returnData')
        else:
            self._print(symbol_info)
            return None

    def in_market_hours(self, symbol):
        """Check if the current symbol is actively trading in its market hours.

        Args:
            symbol ([type]): [description]

        Returns:
            [type]: [description]
        """
        trading_hours = self.commandExecute(
            commandName='getTradingHours', 
            arguments={
                "symbols": [symbol]
            }
        )
        if trading_hours.get('status') == True:
            return trading_hours.get('returnData')
        else:
            self._print(trading_hours)
            return None

    
    def get_margin_requirement(self, ticker, size):
        margin_req = self.commandExecute(
            commandName='getMarginTrade', 
            arguments={
                "symbol": ticker,
                "volume": size
            }
        )

        if margin_req.get('status') == True:
            return margin_req.get('returnData').get('margin')
        else:
            self._print(margin_req)
            return None

    # ====================== #
    # PRICE INFO
    # ====================== #
    def get_tick_price(self, ticker, since):
        price_data = self.commandExecute(
            commandName = 'getTickPrices',
            arguments={
                'info' : {
                    "level" : 0,
                    "symbol" : [ticker],
                    "timestamp" : since.timestamp()*1000
                } 
            }
        )
        if price_data.get('status') == True:
            price_data = pd.json_normalize(
                price_data.get('returnData').get('quotations')
            )
            return price_data
        else:
            self._print(price_data)
            return pd.DataFrame()

    # 
    def get_open_positions(self):
        open_trades = self.commandExecute(
            commandName = 'getTrades',
            arguments = {'openedOnly' : True}
        )
        if open_trades.get('status') == True:
            open_trades = open_trades.get('returnData')
            return open_trades
        else:
            self._print(open_trades)
            return pd.DataFrame()
