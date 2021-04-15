#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# execution.py
# @author: Darren 
import datetime as dt

from zetatrader.event import FillEvent
from zetatrader.execution_handler.execution import ExecutionHandler

class XtbExecution(ExecutionHandler):
    """Order execution handler for XTB broker. 
    """
    def __init__(self, events, connection):
        self.events = events 
        self.connection = connection
        self.pending_orders = []
        self.type_dict = {
            'BUY': 0
            , 'SELL': 1
            , 'BUY_LIMIT': 2
            , 'SELL_LIMIT': 3
            , 'BUY_STOP': 4
            , 'SELL_STOP': 5
        }
        self.task_dict = {
            'OPEN': 0
            , 'CLOSE': 2
            , 'MODIFY': 3
            , 'DELETE': 4
        }
        self.order_status_dict = {
            0: 'ERROR'
            , 1: 'PENDING'
            , 3: 'ACCEPTED'
            , 4: 'REJECTED'
        }

    def execute_pending_orders(self):
        """
        Send any Orders in backlog to be executed. 
        """
        if self.pending_orders:
            pending_orders = self.pending_orders.copy()
            self.pending_orders = []
            for order in pending_orders:
                self.execute_order(order)

    def execute_order(self, event):
        """Sends order to XTB Brokerage 

        Args:
            event (OrderEvent): Object with order specific information
        """
        if event.type == 'ORDER':
            if event.isexit == True:
                self.execute_market_exit(event=event)
            elif event.order_type == 'MKT':
                if event.direction == 'BUY':
                    self.execute_market_buy(event=event)
                elif event.direction == 'SELL':
                    self.execute_market_sell(event=event)
            elif event.order_type == 'LIMIT':
                if event.direction == 'BUY':
                    pass
                elif event.direction == 'SELL':
                    pass

    def get_order_status(self, order_number):
        """[summary]

        Args:
            order_number ([type]): [description]

        Returns:
            [dict]: Order status detail
        """
        order_status = self.connection.commandExecute(
            commandName = 'tradeTransactionStatus',
            arguments = {'order' : order_number}
        )
        if order_status.get('status') == True:
            return order_status.get('returnData')
        else:
            raise('Order Status is False')
    
    def get_fill_status(self, fill_number):
        """Finds the execution details for the given order number

        Args:
            fill_number ([type]): order number created by XTB transaction

        Returns:
            [dict]: filled order details 
        """
        fill_status = self.connection.commandExecute(
            commandName = 'getTrades',
            arguments = {'openedOnly' : True}
        )
        # Find order 
        if fill_status.get('status') == True:
            for i in fill_status['returnData']:
                if i['order2'] == fill_number:
                    return i
    
    def get_close_status(self, fill_number):
        """Returns fill status of a trade that has been closed

        Args:
            fill_number ([type]): [description]
        """
        lookback = dt.timedelta(minutes=5)
        fill_status = self.connection.commandExecute(
            commandName = 'getTradesHistory',
            arguments = {
                "end": 0,
                "start": round((dt.datetime.now() - lookback).timestamp()*1000)
            }
        )
        # Find order 
        if fill_status.get('status') == True:
            for i in fill_status['returnData']:
                if i['order2'] == fill_number:
                    return i

    def execute_market_exit(self, event):
        """CLOSE a trade identified by lot_id in Order Event. 

        Args:
            event ([type]): [description]
        """
        order_type = None
        if event.lot_id == 0:
            raise("Fill Id cannot be 0")
        if event.direction == 'BUY':
            order_type = self.type_dict['BUY']
        elif event.direction == 'SELL':
            order_type = self.type_dict['SELL']
        else:
            raise('Incorrect Order Type Given')
        order_args = { 
            'tradeTransInfo' :{
                "cmd": order_type,
                "customComment": "Exit",
                "expiration": 0,
                "offset": 0,
                "order": event.lot_id,
                "price": 1, # Any none zero is fine
                "sl": 0.0,
                "symbol": event.symbol,
                "tp": 0.0,
                "type": self.task_dict['CLOSE'],
                "volume": event.quantity
            }
        }
        send_order = self.connection.commandExecute(
            commandName = 'tradeTransaction',
            arguments = order_args
        )
        if send_order.get('status') == True:
            order_number = send_order.get('returnData').get('order')
            order_status = self.get_order_status(order_number)
            exe_status = order_status.get('requestStatus')
            if self.order_status_dict[exe_status] == 'ACCEPTED':
                pass
            elif self.order_status_dict[exe_status] == 'REJECTED':
                # Store Order 
                print('Order Rejected')
                print('Order Event added pending orders')
                self.pending_orders.append(event)
                raise('Order Rejected')

    def execute_market_buy(self, event):
        """Executes a BUY MARKET order base on order details given in event.
        When the trade is executed, create a FILL event and add it to queue. 

        Args:
            event (EVENT): ORDER event 
        """
        task = None
        if event.lot_id != 0 and event.direction == 'BUY':
            task = self.task_dict['MODIFY']
        elif event.lot_id == 0:
            task = self.task_dict['OPEN']
        
        order_args = {
            'tradeTransInfo' :{
                "cmd": self.type_dict['BUY'],
                "customComment": "ADD COMMENTS",
                "expiration": 0,
                "offset": 0,
                "order": event.lot_id,
                "price": 1, # Any none zero is fine
                "sl": 0.0,
                "symbol": event.symbol,
                "tp": 0.0,
                "type": task,
                "volume": event.quantity
            }
        }

        send_order = self.connection.commandExecute(
            commandName = 'tradeTransaction',
            arguments = order_args
        )

        if send_order.get('status') == True:
            order_number = send_order.get('returnData').get('order')
            order_status = self.get_order_status(order_number)
            exe_status = order_status.get('requestStatus')
            if self.order_status_dict[exe_status] == 'ACCEPTED':
                pass
            elif self.order_status_dict[exe_status] == 'REJECTED':
                print('Order Rejected')
                print('Order Event added pending orders')
                self.pending_orders.append(event)
                raise('Order Rejected')
            elif self.order_status_dict[exe_status] == 'PENDING':
                print('Order Pending')
    
    def execute_market_sell(self, event):
        """Executes a SELL MARKET order base on order details given in event.
        When the trade is executed, create a FILL event and add it to queue. 

        Args:
            event (EVENT): ORDER event 
        """
        task = None
        if event.lot_id != 0 and event.direction == 'SELL':
            task = self.task_dict['MODIFY']
        elif event.lot_id == 0:
            task = self.task_dict['OPEN']
        
        order_args = {
            'tradeTransInfo' :{
                "cmd": self.type_dict['SELL'],
                "customComment": "SELL Order",
                "expiration": 0,
                "offset": 0,
                "order": event.lot_id,
                "price": 1, # Any none zero is fine
                "sl": 0.0,
                "symbol": event.symbol,
                "tp": 0.0,
                "type": task,
                "volume": event.quantity
            }
        }
        send_order = self.connection.commandExecute(
            commandName = 'tradeTransaction',
            arguments = order_args
        )
        
        if send_order.get('status') == True:
            order_number = send_order.get('returnData').get('order')
            order_status = self.get_order_status(order_number)
            exe_status = order_status.get('requestStatus')
            if self.order_status_dict[exe_status] == 'ACCEPTED':
                pass
            elif self.order_status_dict[exe_status] == 'REJECTED':
                print('Order Rejected')
                print('Order Event added pending orders')
                self.pending_orders.append(event)
                raise('Order Rejected')
            elif self.order_status_dict[exe_status] == 'PENDING':
                print('Order Pending')
                return None

import os 
# Import Own Modules
from zetatrader.xtb.api import XRest
from zetatrader.event import OrderEvent
from zetatrader.xtb.execution import XtbExecution

class DummieEvents:
    def __init__(self):
        self.items = []

    def put(self, x):
        self.items.append(x)

    def get(self):
        if self.items:
            return self.items.pop(0)

if __name__ == '__main__':
    demo_port = 5124
    client =  XRest(os.environ.get('XTB_DEMO_USER'), os.environ.get('XTB_DEMO_PW'), islive=False)
    queue = DummieEvents()
    ex = XtbExecution(queue, client)
    order = OrderEvent('EURUSD', 'MKT', 0.05, 'SELL')
    # Buy 
    ex.execute_order(order)

    # Partial Exit Trade
    position = queue.get()
    order = OrderEvent('EURUSD', 'MKT', 0.01, 'BUY', lot_id=position.lot_id, isexit=True)
    execution = ex.execute_order(order)
    client.disconnect()