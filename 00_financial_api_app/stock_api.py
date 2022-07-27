import numpy as np
import json 
import http.client
from datetime import datetime

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

    def __init__(self, StockName):
         self.conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
         self.headers = {'x-rapidapi-key': "  ", 'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"}
         self.StockName= StockName
         self.collected_data=[]
         self.stocks_and_returns= dict()
         
    def getYahooAPI(self):
        """
        Performs the calculations to return the metrics defined on the class for each stock on the list given by the user
        """
        self.conn.request("GET", "/stock/v3/get-historical-data?symbol=" + self.StockName + "&region=US", headers=self.headers)
        res = self.conn.getresponse()
        data = res.read()
        json_data= json.loads(data)
        local_price_list= json_data['prices']
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
        now = datetime.now()
        results= dict({"Stock": self.StockName,
                      "Date of Query": now.strftime("%d/%m/%Y %H:%M:%S"),
                      "Yearly Return": yearly_return,
                      "Mean Price": mean_price,
                      "Minimun Price":minimun_price,
                      "Maximun Price": maximun_price,
                      "Standard Deviation": standard_deviation})
        return results

    #I am buying at the lower price of the opening day
    def get_transaction_price(self, stock_name, transaction_type):
        self.conn.request("GET", "/stock/v3/get-historical-data?symbol=" + stock_name + "&region=US", headers=self.headers)
        res = self.conn.getresponse()
        data = res.read()
        json_data= json.loads(data)
        if transaction_type == "buy":
            return json_data["prices"][0]["open"]
        return json_data["prices"][0]["close"]
    


