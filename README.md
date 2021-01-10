# zetatrader
zetatrader is a Python library for algorithimic trading. It has 3 packages
tradinginfrastructure, datainfrastructure, and zetatrader. zetatrader package
consist of the trading strategy that utilizes the other packages to conduct 
algo trading and research.

## requirements
python3.x

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
The library can be broken down into 3 diferent package. The 
tradinginfrastructure package consist of modules that makes up
the trading engine. 

The datainfrastructure package makes up the 
modules that lets up update and interact with our mysql securities
database to conduct research. 

Lastly, zetatrade consist holds the actual trading strategy algo 
and utilizes tradinginfrastructure as the engine to backtest and
conduct live trading.

## Directory 
.
 |--- tradinginfrastructure <- Class objects for the event trading program
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
 |--- zetatrader
 |    | # Folders to different trading strategies
 |
 |
 |--- datainfrastructure
 |    |--- sec_db.py
 |    |--- tiingo.py
 |    |--- credentials_template.py
 |
 |--- setup.py
 |--- .gitignore
 |--- README.md

## Credits
Dr. Michael Moore at Quantstart who inspired my choice to write the algo
in the form of a event-driven system.


