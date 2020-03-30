#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# money_management.py
# Darren Jun Yi Yeap 03/07/2020
from tradingframework.event import OrderEvent

class RiskManager:
    """Encapsules the interaction between a portfolio and its hard risk limits.
    If a risk limit will be breached by a new order, the order will be resized
    or cancled. 
    """
    def __init__(self):
        pass
