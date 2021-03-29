# zetatrader
zetatrader is a Python library for algorithimic trading. It is a event-driven 
trading/backtesting engine. 

## requirements
python3.8 or above

## Installation
Use the package manager to install package in your python environment.
"pip3 install -e ." lets you install the package in a development 
environment and use. Run  the folder zetatrader folder.  

```bash 
pip3 install -e .
#OR 
pip3 install -e zetatrader
```

## Usage
The library consist of an event-driven trading engine that can be run by using the TradingSession object in trading_session. TradingSession requires a PriceHandler object, ExecutionHandler object, Book object, Portfolio object, Strategy Object, MoneyManagement object, RiskManager object, and Performance object. All of these objects can be imported from within this package. 

## Directory 
 |--- zetatrader <- Class objects for the event trading program\
 |    |--- book\
 |    |    |--- book.py\
 |    |--- execution_handler\
 |    |    |--- execution.py<br>
 |    |--- performance\
 |    |    |--- trading_stats.py<br> 
 |    |--- portfolio\
 |    |    |--- portfolio.py<br> 
 |    |--- price_handler\
 |    |    |--- db_price_handler.py<br> 
 |    |--- strategy\
 |    |    |--- base.py <br>
 |    |--- event.py\
 |    |--- money_management.py\
 |    |--- risk_manager.py\
 |    |--- trading_session.py\
 |\
 |--- setup.py\
 |--- .gitignore\
 |--- README.md\

## Credits
Dr. Michael Moore at Quantstart who inspired my choice to write the algo in the form of a event-driven system.


