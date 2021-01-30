# zetatrader
zetatrader is a Python library for algorithimic trading. It is a event-driven 
trading engine. 

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
The library consist of an event-driven trading engine that can be run by using the TradingSession object in trading_session. TradingSession requires a PriceHandler object, ExecutionHandler object, Book object, Portfolio object, Strategy Object, MoneyManagement object, RiskManager object, and Performance object. All of these objects can be imported from within this package, but you can write your own custom components to fit your trading objectives. 

## Directory 
 |--- zetatrader <- Class objects for the event trading program
 |    |--- book
 |    |    |--- book.py
 |    |--- execution_handler
 |    |    |--- execution.py 
 |    |--- performance
 |    |    |--- execution.py 
 |    |--- portfolio
 |    |    |--- execution.py 
 |    |--- price_handler
 |    |    |--- execution.py 
 |    |--- strategy
 |    |    |--- execution.py 
 |    |--- event.py
 |    |--- money_management.py
 |    |--- risk_manager.py
 |    |--- trading_session.py
 |
 |--- setup.py
 |--- .gitignore
 |--- README.md
 |--- credentials.py

## Credits
Dr. Michael Moore at Quantstart who inspired my choice to write the algo in the form of a event-driven system.


