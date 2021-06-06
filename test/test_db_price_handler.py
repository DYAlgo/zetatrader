#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import os
import unittest
import datetime as dt

# Import own module
from zetatrader.price_handler.db_price_handler import DbPriceHandler


class TestDbPriceHandler(unittest.TestCase):
    def test_construct_symbol_data(self):
        price_handler = DbPriceHandler(
            "MARKET_EVENT",
            {"AAPL": 3656, "EWM": 7231},
            start_dt=dt.datetime(2019, 5, 1),
            end_dt=dt.datetime(2020, 12, 1),
            db_user=os.environ.get("SEC_DB_USER"),
            db_password=os.environ.get("SEC_DB_PW"),
            frequency="daily",
        )

        # Check that both price_data have same length
        self.assertEqual(
            len(price_handler.symbol_data.get("AAPL")),
            len(price_handler.symbol_data.get("EWM")),
        )
        # Check that both have the same date at row 100
        self.assertEqual(
            price_handler.symbol_data.get("AAPL")["price_date"][100],
            price_handler.symbol_data.get("EWM")["price_date"][100],
        )

        # Check that both have the same date at row 200
        self.assertEqual(
            price_handler.symbol_data.get("AAPL")["price_date"][200],
            price_handler.symbol_data.get("EWM")["price_date"][200],
        )

        print("test_construct_symbol_data done!")

    def test_latest_bar(self):
        price_handler = DbPriceHandler(
            "MARKET_EVENT",
            {"AAPL": 3656, "EWM": 7231},
            start_dt=dt.datetime(2019, 5, 1),
            end_dt=dt.datetime(2020, 12, 1),
            db_user=os.environ.get("SEC_DB_USER"),
            db_password=os.environ.get("SEC_DB_PW"),
            frequency="daily",
        )

        # Check that close price on
        price_handler.bar_index = 1
        self.assertEqual(price_handler.get_latest_bar("EWM")["close_price"], 29.32)
        self.assertEqual(price_handler.get_latest_bar("AAPL")["close_price"], 209.15)

        print("test_latest_bar done!")

    def test_latest_bars(self):
        price_handler = DbPriceHandler(
            "MARKET_EVENT",
            {"AAPL": 3656, "EWM": 7231},
            start_dt=dt.datetime(2019, 5, 1),
            end_dt=dt.datetime(2020, 12, 1),
            db_user=os.environ.get("SEC_DB_USER"),
            db_password=os.environ.get("SEC_DB_PW"),
            frequency="daily",
        )

        # Base case: there is enough bars to look back
        price_handler.bar_index = 4
        self.assertEqual(len(price_handler.get_latest_bars("AAPL", 5)), 5)

        self.assertEqual(len(price_handler.get_latest_bars("AAPL", 10)), 5)

        print("test_latest_bars done!")

    def test_get_latest_bar_datetime(self):
        price_handler = DbPriceHandler(
            "MARKET_EVENT",
            {"AAPL": 3656, "EWM": 7231},
            start_dt=dt.datetime(2019, 5, 1),
            end_dt=dt.datetime(2020, 12, 1),
            db_user=os.environ.get("SEC_DB_USER"),
            db_password=os.environ.get("SEC_DB_PW"),
            frequency="daily",
        )
        price_handler.bar_index = 0
        self.assertEqual(
            price_handler.get_latest_bar_datetime("EWM"), dt.datetime(2019, 5, 1)
        )
        price_handler.bar_index = 1
        self.assertEqual(
            price_handler.get_latest_bar_datetime("EWM"), dt.datetime(2019, 5, 2)
        )

        print("test_get_latest_bar_datetime done!")

    def test_get_latest_bar_value(self):
        price_handler = DbPriceHandler(
            "MARKET_EVENT",
            {"AAPL": 3656, "EWM": 7231},
            start_dt=dt.datetime(2019, 5, 1),
            end_dt=dt.datetime(2020, 12, 1),
            db_user=os.environ.get("SEC_DB_USER"),
            db_password=os.environ.get("SEC_DB_PW"),
            frequency="daily",
        )
        price_handler.bar_index = 10
        self.assertEqual(
            price_handler.get_latest_bar_value("AAPL", "close_price"), 190.92
        )

    def test_get_latest_bar_values(self):
        price_handler = DbPriceHandler(
            "MARKET_EVENT",
            {"AAPL": 3656, "EWM": 7231},
            start_dt=dt.datetime(2019, 5, 1),
            end_dt=dt.datetime(2020, 12, 1),
            db_user=os.environ.get("SEC_DB_USER"),
            db_password=os.environ.get("SEC_DB_PW"),
            frequency="daily",
        )
        price_handler.bar_index = 10
        self.assertEqual(
            len(price_handler.get_latest_bars_values("AAPL", "close_price", 11)), 11
        )
        self.assertEqual(
            len(price_handler.get_latest_bars_values("AAPL", "close_price", 15)), 11
        )
        print("test_get_latest_bar_values done!")


if __name__ == "__main__":
    test = TestDbPriceHandler()
    test.test_construct_symbol_data()
    test.test_latest_bar()
    test.test_latest_bars()
    test.test_get_latest_bar_datetime()
    test.test_get_latest_bar_values()
