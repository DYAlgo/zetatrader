import unittest
import pandas as pd
import datetime as dt
from tradingframework.event import FillEvent
from tradingframework.price_handler.base import AbstractPriceHandler
from tradingframework.book.book import Book

class MockPriceHandler(AbstractPriceHandler):
    """Mimicks a price handler that feeds prices set by user for 
    testing purposes. First bar is set to some arbitrary price.  
    Second day price is set to increase. 
    Third day bars are set to have splits and the last bar it set 
    with a dividend payment. 
    """
    def __init__(self):
        """Initializes the object"""
        self.symbol_list = [69, 96]
        self.index = 0

        self.price_data={
            69: pd.DataFrame({
                'datetime':[dt.datetime(2019,1,1), dt.datetime(2019,1,2)
                    , dt.datetime(2019,1,3), dt.datetime(2019,1,4)]
                ,'close_price':[100.0, 101.0, 50.5, 50.5]
                ,'split':[1.0, 1.0, 2.0, 1.0]
                ,'dividend':[0.0, 0.0, 0.0, 1.0]
            })
            , 96: pd.DataFrame({
                'datetime':[dt.datetime(2019,1,1), dt.datetime(2019,1,2)
                    , dt.datetime(2019,1,3), dt.datetime(2019,1,4)]
                ,'close_price':[300.0, 301.0, 60.2, 60.2]
                ,'split':[1.0, 1.0, 5.0, 1.0]
                ,'dividend':[0.0, 0.0, 0.0, 3]
            })
        }
    
    def set_bar_index(self, index_val):
        """Set index of bar 0 to 4 to use for testing.

        First bar is just lowest price with no other activity
        Second bar has higher price with no other activity
        Third bar is second bar price with stock split
        Fourth bar is a bar with same price as second bar with dividends
        
        Arguments:
            index_val {int} -- The index to set.
        """
        self.index = index_val

    def get_datetime(self):
        return self.price_data[self.symbol_list[0]]['datetime'][self.index]

    def get_latest_bar_split(self, symbol):
        return self.price_data[symbol]['split'][self.index]

    def get_latest_bar_dividend(self,symbol):
        return self.price_data[symbol]['dividend'][self.index]

    def get_latest_bar_value(self, symbol, value):
        return self.price_data[symbol][value][self.index]

    

class TestBook(unittest.TestCase):
    """Create a test to verify the book module is working correctly.
    
    Test covers update timeindex, update position from fill
    update holdings from fill.  
    
    Arguments:
        unittest {[type]} -- [description]
    """
    def setUp(self):
        """Setup mock book by creating a book with  
        """
        self.price_handler = MockPriceHandler()

    def test_update_timeindex(self):
        """Test 
        """     
        # Create a book object.
        book_a = Book(500000, self.price_handler, 'backtest')
        # Test initial setup
        self.assertEqual(book_a.all_positions[0][69], 0)
        self.assertEqual(book_a.all_holdings[0]['cash'], 500000)

        # Update index and see if it changes any portfolio value
        book_a.update_timeindex()
        self.assertEqual(book_a.all_positions[1][69], 0) 
        self.assertEqual(book_a.all_holdings[1][69], 0) 
        self.assertEqual(book_a.all_positions[1][96], 0)
        self.assertEqual(book_a.all_holdings[1][96], 0)
        self.assertEqual(book_a.all_holdings[1]['cash'], 500000)
        self.assertEqual(book_a.all_holdings[1]['total'], 500000)


        # Set up one long 100 unit position in each symbol at end of bar one
        fill_a = FillEvent('', 69, '', 100, 1, 100)
        fill_b = FillEvent('', 96, '', 100, 1, 300)
        self.price_handler.set_bar_index(0)
        cost = fill_a.direction * fill_a.quantity * fill_a.fill_cost
        book_a.current_positions[69] = fill_a.direction * fill_a.quantity
        book_a.current_holdings[69] += cost
        book_a.current_holdings['commission'] += 0
        book_a.current_holdings['cash'] -= cost
        book_a.current_holdings['total'] -= cost
        cost = fill_b.direction * fill_b.quantity * fill_b.fill_cost
        book_a.current_positions[96] = fill_b.direction * fill_b.quantity
        book_a.current_holdings[96] += cost
        book_a.current_holdings['commission'] += 0
        book_a.current_holdings['cash'] -= cost
        book_a.current_holdings['total'] -= cost

        # Update timeindex base on second bar then test value
        self.price_handler.set_bar_index(1)
        book_a.update_timeindex()
        self.assertEqual(book_a.all_positions[-1][69], 100) 
        self.assertEqual(book_a.all_holdings[-1][69], 10100) 
        self.assertEqual(book_a.all_positions[-1][96], 100)
        self.assertEqual(book_a.all_holdings[-1][96], 30100)
        self.assertEqual(book_a.all_holdings[-1]['cash'], 460000)
        self.assertEqual(book_a.all_holdings[-1]['total'], 500200)

        # Update timeindex based on third bar (split) then test
        self.price_handler.set_bar_index(2)
        book_a.update_timeindex()
        self.assertEqual(book_a.all_positions[3][69], 200) 
        self.assertEqual(book_a.all_holdings[3][69], 10100) 
        self.assertEqual(book_a.all_positions[3][96], 500)
        self.assertEqual(book_a.all_holdings[3][96], 30100)
        self.assertEqual(book_a.all_holdings[3]['cash'], 460000)
        self.assertEqual(book_a.all_holdings[3]['total'], 500200)

        # Update timeindex based on fourth bar (dividend) then test
        self.price_handler.set_bar_index(3)
        book_a.update_timeindex()
        self.assertEqual(book_a.all_positions[4][69], 200) 
        self.assertEqual(book_a.all_holdings[4][69], 10100) 
        self.assertEqual(book_a.all_positions[4][96], 500)
        self.assertEqual(book_a.all_holdings[4][96], 30100)
        self.assertEqual(book_a.all_holdings[4]['cash'], 461700)
        self.assertEqual(book_a.all_holdings[4]['total'], 501900)


    def test_update_positions_from_fill(self):
        """[summary]
        """
        # Create a book object
        book_b = Book(500000, self.price_handler, 'backtest') 

        # Create a fill order
        fill_a = FillEvent('', 69, '', 100, 'BUY', 100)

        # Parse fill order through test_update_positions_from_fill
        book_b.update_positions_from_fill(fill_a)
        
        # Check value accuracy
        self.assertEqual(book_b.current_positions[69], 100) 
    
    def update_holdings_from_fill(self):
        """[summary]
        """
        # Create a book object
        book_b = Book(500000, self.price_handler, 'backtest')  

        # Create a fill order 
        fill_a = FillEvent('', 96, '', 100, 'BUY', 300)

        # Parse fill order through test_update_holdings_from_fill
        book_b.update_holdings_from_fill(fill_a)

        # Check value accuracy
        self.assertEqual(book_b.current_holdings[96], 10000) 
        self.assertEqual(book_b.current_holdings['commission'], 0) 
        self.assertEqual(book_b.current_holdings['cash'], 490000)
        self.assertEqual(book_b.current_holdings['total'], 490000)



if __name__ == "__main__":
    unittest.main()