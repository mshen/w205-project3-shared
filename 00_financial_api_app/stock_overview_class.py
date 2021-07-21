import numpy as np
import json 
import http.client


class GetStockReturns(): 
    """
    This class allows you to query the prices of the selected stocks from the YahooFinance API provided by APIDojo,
    For each stock, it returns the following metrics comprised in a dictionary for the most recent year before your query:
        - Yearly return
        - The mean price 
        - The minimun price
        - The maximun price
        - The standard deviation of the price
    """ 

    def __init__(self, ListofStocks):
         self.conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
         self.headers = {'x-rapidapi-key': "3363397742msha214802cd1fc8ecp19357bjsn198d6fb54410", 'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"}
         self.ListofStocks= ListofStocks
         self.collected_data=[]
         self.stocks_and_returns= dict()
         
    def getYahooAPI(self):
       """
       Performs the calculations to return the metrics defined on the class for each stock on the list given by the user
       """
       for symbol in self.ListofStocks: 
           self.conn.request("GET", "/stock/v3/get-historical-data?symbol=" + symbol + "&region=US", headers=self.headers)
           res = self.conn.getresponse()
           data = res.read()
           json_data= json.loads(data)
           self.collected_data.append(json_data)
           
       for stock in range(len(self.collected_data)):
               stock_name= self.ListofStocks[stock]
               local_price_list= self.collected_data[stock]['prices']
               price_and_dates=[]
               
               for j in range(len(local_price_list)):
                   price_and_dates.append([local_price_list[j].get('date'), local_price_list[j].get('adjclose')])
               price_and_dates= np.array(price_and_dates)
               
               #Eliminating NonType objects of the numpy array
               None_index=[]
               for index,value in enumerate(price_and_dates): 
                   if value[1]==None: 
                       None_index.append(index)
                       
               if len(None_index)>0:
                   price_and_dates = np.delete(price_and_dates, None_index, axis=0)
               #Calculating the yearly returns of the stock and other metrics and storing it in a dictionary
               recent_price= price_and_dates[0][1]
               oldest_price= price_and_dates[len(price_and_dates)-1][1]
               yearly_return= (recent_price-oldest_price)/oldest_price
               standard_deviation= np.std(price_and_dates, axis=0, dtype=np.float64)[1]
               mean_price= np.mean(price_and_dates, axis=0, dtype=np.float64)[1]
               minimun_price= np.min(price_and_dates, axis=0)[1]
               maximun_price= np.max(price_and_dates, axis=0)[1]
               #Creation of the dictionary containing the data
               self.stocks_and_returns[stock_name]= (yearly_return,mean_price,minimun_price,maximun_price,standard_deviation)
               
    def __str__(self):
        return 'This is a portfolio comprised of the Stocks:' + ' ' + ','.join(self.ListofStocks)
    



