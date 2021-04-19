#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import os
import unittest
import datetime as dt
# From 
from zetatrader.xtb.api import XRest
from zetatrader.xtb.price_data import PriceData

class DummieEvents:
    def __init__(self):
        self.items = []

    def put(self, x):
        self.items.append(x)

    def get(self):
        if self.items:
            return self.items.pop(0)

class TestPriceData(unittest.TestCase):
    def test_construct_symbol_data(self):
        client = XRest(os.environ.get('XTB_DEMO_USER'), os.environ.get('XTB_DEMO_PW'))
        handler = PriceData(DummieEvents(), ['EURUSD'], client, '1MIN')
        self.assertListEqual(
            list(handler.symbol_data['EURUSD'].columns),
            ['price_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
        )
        self.assertEqual(
            type(handler.symbol_data['EURUSD'].loc[0, 'price_date'])
            , type(dt.datetime(2020,1,1))
        )
        print('TestPriceData OK!')

    def test_latest_bar(self):
        pass

    def test_latest_bars(self):
        pass

    def test_get_latest_bar_value(self):
        pass

    def test_get_latest_bar_values(self):
        pass
