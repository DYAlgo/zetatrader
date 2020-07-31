#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import pymysql
from dataframework.credentials import sec_db_cred


class SecDbConn:
    """sec_db mysql connection class
    """
    def __init__(self, cred=sec_db_cred):
        self.host=cred['db_host']
        self.username=cred['db_user']
        self.password=cred['db_pass']
        self.dbname=cred['db_name']
        self.conn=None
        print("SecDbConn object created.")

    def open_connection(self):
        """Connect to the Sec_DB Database
        """
        try:
            if self.conn is None:
                self.conn = pymysql.connect(
                    host = self.host
                    , user = self.username
                    , passwd = self.password
                    , db = self.dbname
                ) 
                #print('Connection Opened')
                # Add logging here 
        except pymysql.MySQLError as e:
            print('Error: %s'%e)
            #Add logging here 
            sys.exit()
    
    def close_connection(self):
        """Close the connection if it is not already closed
        """
        if self.conn != None and self.conn.open == True:
            self.conn.close()
            self.conn=None
            #print('Connection Closed')