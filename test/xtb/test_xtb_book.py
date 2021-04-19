#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import os
from zetatrader.xtb.api import XRest
from zetatrader.xtb.book import XtbBook
from zetatrader.xtb.price_data import PriceData
from zetatrader.xtb.execution import XtbExecution

class DummieEvents:
    def __init__(self):
        self.items = []

    def put(self, x):
        self.items.append(x)

    def get(self):
        if self.items:
            return self.items.pop(0)
        else:
            return None

if __name__ == '__main__':
    queue = DummieEvents()
    client = XRest(os.environ.get('XTB_DEMO_USER'), os.environ.get('XTB_DEMO_PW'))
    handler = PriceData(DummieEvents(), ['EURUSD', 'GOLD'], client, '1DAY')
    ex = XtbExecution(queue, client)
    ledger = XtbBook(queue, handler, client)
    ledger.update_timeindex()

    # Exit Half 0.5 Units of GOLD
    ledger.reduce_positon('GOLD', 0.33354)
    while True:
        order = queue.get()
        if order == None:
            break 
        else:
            ex.execute_order(order)
    ledger.update_timeindex()

    # Exit All of OIL
    ledger.close_position('EURUSD')
    while True:
        order = queue.get()
        if order == None:
            break 
        else:
            ex.execute_order(order)
    ledger.update_timeindex()

    # Establish new position
    ledger.add_position('EURUSD', 0.5, 'BUY')
    while True:
        order = queue.get()
        if order == None:
            break 
        else:
            ex.execute_order(order)
    ledger.update_timeindex()
    print('')