#!/usr/bin/env python
import json
import time
from kafka import KafkaProducer
from flask import Flask, request, jsonify
from  stock_api import *

app = Flask(__name__)
producer = KafkaProducer(bootstrap_servers='kafka:29092')

## This is for the use of kafka in the container

def log_to_kafka(topic, event):
     event.update(request.headers)
     producer.send(topic, json.dumps(event).encode())


@app.route("/")
def default_response():
    default_event = {'event_type': 'default instructions'}
    log_to_kafka('default_call', default_event)
    return ('If you want to consult the yearly return of a stock go to the following route: /stock name\n If you want to consult a metric go to the \
            following route: /stockName/metric' )


@app.route("/<stock_name>")
def testing_stock(stock_name):
    #Calling the Yahoo finance API
    stock_overview= GetStockReturns(stock_name)
    result= stock_overview.getYahooAPI()
    
    #Sending the event to kafka
    stock_request_event = {'event_type': 'check_stock_{}'.format(stock_name),'stock_name': stock_name, "query_timestamp" : time.time() * 1000}
    print(stock_request_event)
    log_to_kafka('stock_call', stock_request_event)
    #log_to_kafka('stock_results', result)

    #Final return to the user
    return result

@app.route("/<stock_name>/<action>/<quantity>",methods = ['POST'])
def action_stock(stock_name,action,quantity):
    stock_overview = GetStockReturns(stock_name)
    if action == "buy":
        buy_price = stock_overview.get_transaction_price(stock_name,action)
        stock_transaction_event = {
            'event_type': '{}_{}'.format(action, stock_name),
            'stock_name': stock_name,
            'price': buy_price,
            'quantity': int(quantity),
            'transaction_amount' : buy_price * int(quantity),
            "transaction_timestamp" : time.time() * 1000
        }
        
        log_to_kafka('stock_operation',  stock_transaction_event)
        return jsonify({"task": "bought_{}_{}".format(quantity,stock_name)}), 201
    
    if action == "sell":
        sell_price = stock_overview.get_transaction_price(stock_name, action)
        stock_transaction_event = {
            "event_type": "{}_{}".format(action, stock_name),
            'stock_name': stock_name,
            "price": sell_price,
            "quantity": int(quantity),
            "transaction_amount" : sell_price * int(quantity),
            "transaction_timestamp" : time.time() * 1000
        }
        log_to_kafka('stock_operation',  stock_transaction_event)
        return jsonify({"task": "sold_{}_{}".format(quantity, stock_name)}), 201


if __name__ == '__main__':
    app.debug=True
    app.run()

