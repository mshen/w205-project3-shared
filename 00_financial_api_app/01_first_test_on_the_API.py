#!/usr/bin/env python
import json
#from kafka import KafkaProducer
from flask import Flask, request
from  stock_overview_class import *


app = Flask(__name__)
#producer = KafkaProducer(bootstrap_servers='kafka:29092')

##This is for the use of kafka in the container
# =============================================================================
# def log_to_kafka(topic, event):
#     event.update(request.headers)
#     producer.send(topic, json.dumps(event).encode())
# 
# =============================================================================

@app.route("/")
def default_response():
    default_event = {'event_type': 'default instructions'}
    #log_to_kafka('events', default_event)
    return ('If you want to consult the yearly return of a stock go to the following route: /stock name\n If you want to consult a metric go to the \
            following route: /stockName/metric' )


@app.route("/<stock_name>")
def testing_stock(stock_name):
    #Parsing the given stock
    stock_list= stock_name.split(',')
    #Calling the Yahoo finance API
    stock_overview= GetStockReturns(stock_list)
    stock_overview.getYahooAPI() 
    result= stock_overview.stocks_and_returns
    
    #Sending the event to kafka
    stock_request_event = {'event_type': 'calling for stock {}'.format(stock_name)}
    #log_to_kafka('events', stock_request_event)
    yearly_return= result[stock_name][0]
    #Final return to the user
    return result


if __name__ == '__main__':
    app.debug=True
    app.run()
    



# =============================================================================
# ##Testing
# stock_name= 'AMZN'
# stock_list= stock_name.split(',')
# stock_overview= GetStockReturns(stock_list)
# stock_overview.getYahooAPI() 
# 
# result= stock_overview.stocks_and_returns
# =============================================================================

# =============================================================================
# @app.route("/<stock_name>/<metric>")
# def testing_stock(stock_name, metric):
#     
#     #Sending the event to kafka
#     stock_request_event = {'event_type': 'calling for stock {}'.format(stock_name)}
#     #log_to_kafka('events', stock_request_event)
#     
#     #Parsing the given stock
#     stock_list= stock_name.split(',')
#     
#     #Calling the Yahoo finance API
#     stock_overview= GetStockReturns(stock_list)
#     stock_overview.getYahooAPI() 
#     result= stock_overview.stocks_and_returns 
# =============================================================================

# =============================================================================
#     
#     if metric='mean_price':
#         return
#     
# =============================================================================





    
    
# =============================================================================
#     
#     #Final return to the user
#     return result
# =============================================================================




##This is a very important thing to have since it will run the application after you pass it in the CLI, or 
# as I prefer the ANACONDA PROMPT HAHAHA

    
    
    



# =============================================================================
# yearly_return= result[stock_name][0]
# mean_price= result[stock_name][1]
# minimun_price= result[stock_name][2]
# maximun_price= result[stock_name][3]
# standard_deviation=  result[stock_name][5]
# =============================================================================

