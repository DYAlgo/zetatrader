#!/usr/bin/env python3

# tiingo.py
# Author: Darren Jun Yi Yeap
# Version 0.1

import pandas as pd
import io
import numpy as np
import datetime as dt
import requests
import time
from credentials import tiingo_api_key

class Tiingo:
	"""
	Creates an object with API connection to Tiingo server and provides
	functions to pull data from Tiingo.

	NOTE: 
	Functions that pulls in data with datetime that is more specific 
	than yyyy-mm-dd, must not make request through csv format as it 
	will only show up in the form of string yyyy-mm-dd.
	"""
	def __init__(self, key=tiingo_api_key):
		"""
		Initialize the object
		key: the api key for the users Tiingo account
		"""
		self.key = str(key['key'])

	def get_data(self, ticker, start_date, end_date, time_frame = 'daily'):
		"""
		Returns all of the given stocks daily data that fall within 
		the start and end date.

		Parameters:
		ticker - the current stock ticker/ symbol
		start_date - the start date in yyyy-mm-dd format
		end_date - the end date in yyyy-mm-dd format
		time_frame - bar interval (daily, weekly, monthly)
		"""
		url = ('https://api.tiingo.com/tiingo/daily/'
			'%s/prices?startDate=%s'
			'&endDate=%s&format=csv&resampleFreq=%s'
			'&token=') %(ticker, start_date, end_date, 
			time_frame)
		my_request = requests.get(str(url+self.key)).content
		csv_data = pd.read_csv(io.StringIO(my_request.decode('utf-8')))  
		csv_data = csv_data[['date', 'open', 'high', 'low', 'close', 'adjClose'
			, 'volume', 'divCash', 'splitFactor']]
		csv_data['date'] = csv_data['date'].astype('datetime64[ns]') 
		return csv_data
        
    
	def get_all_data(self, ticker, time_frame = 'daily'):
		'''Returns all of the given stocks daily data
		Parameters:
		ticker - the current stock ticker/ symbol
		time_frame - bar interval (daily, weekly, monthly)'''
		# Earliest start date possible
		start_date = '0001-01-01'
		url = ('https://api.tiingo.com/tiingo/daily/'
			'%s/prices?startDate=%s&format=csv&resampleFreq=%s'
			'&token=') %(ticker, start_date, 
			time_frame)
		
		my_request = requests.get(str(url+self.key)).content  
		csv_data = pd.read_csv(io.StringIO(my_request.decode('utf-8')))
		csv_data = csv_data[['date', 'open', 'high', 'low', 'close', 'adjClose'
			, 'volume', 'divCash', 'splitFactor']] 
		csv_data['date'] = csv_data['date'].astype('datetime64[ns]') 
		return csv_data		  





if __name__ == "__main__":
	t = Tiingo()
	print( t.get_all_data("MMM").head() )
	print(t.get_all_data("MMM").loc[0, 'date'])
	print(type( t.get_all_data("MMM").loc[0, 'date'] ))
	print( t.get_all_data("MMM").loc[0, 'date'].to_pydatetime() )
	

