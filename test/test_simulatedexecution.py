#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import unittest
import datetime as dt

# Import own modules
from zetatrader.event import OrderEvent
from zetatrader.execution_handler.execution import SimulatedExecution


class DummiePriceHandler:
    def __init__(self):
        self.symbol_name = "AAPL"
        self.return_next_open = True

    def get_next_open_price(self, symbol):
        if self.return_next_open == True:
            return 103
        else:
            raise KeyError

    def get_latest_bar_datetime(self, symbol):
        if symbol == "AAPL":
            return dt.datetime(2020, 1, 1)

    def get_latest_bar_value(self, symbol, value_name):
        if value_name == "close_price" and symbol == self.symbol_name:
            return 99.8


class DummieEvents:
    def __init__(self) -> None:
        self.item_list = []

    def put(self, item):
        self.item_list.append(item)

    def get(self):
        return self.item_list.pop(0)


class TestSimulatedExecution(unittest.TestCase):
    def test_execute_order_on_close(self):
        # Create Dummie Price Handler
        event_handler = DummieEvents()
        price_handler = DummiePriceHandler()
        order_1 = OrderEvent("AAPL", "MKT", 5, "SELL")
        executor = SimulatedExecution(
            event_handler, price_handler, on_open=False, commission=1
        )

        executor.execute_order(order_1)

        # Check EVENT handler
        fill = event_handler.get()
        self.assertEqual(fill.symbol, "AAPL")
        self.assertEqual(fill.direction, "SELL")
        self.assertEqual(fill.quantity, 5)
        self.assertEqual(fill.fill_cost, 99.8)
        self.assertEqual(fill.commission, 1)
        print("Execute on close works")

    def test_execute_order_on_next_open(self):
        # Create Dummie Price Handler
        event_handler = DummieEvents()
        price_handler = DummiePriceHandler()
        order_1 = OrderEvent("AAPL", "MKT", 7, "BUY")
        executor = SimulatedExecution(
            event_handler, price_handler, on_open=True, commission=1
        )

        executor.execute_order(order_1)

        # Check EVENT handler
        fill = event_handler.get()
        self.assertEqual(fill.symbol, "AAPL")
        self.assertEqual(fill.direction, "BUY")
        self.assertEqual(fill.quantity, 7)
        self.assertEqual(fill.fill_cost, 103)
        self.assertEqual(fill.commission, 1)
        print("Execute on next open works")


if __name__ == "__main__":
    test = TestSimulatedExecution()
    test.test_execute_order_on_close()
    test.test_execute_order_on_next_open()
