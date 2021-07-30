## Understanding User Behaviour

In this project we work for a company that advices customers whether to invest or not invest in certain technological stocks. Since the onset of the covid-19 pandemic, the stock market has had to deal with some drastic changes of its own. In this project we aim to analyze user behavior, in particular understand the trends of buying/selling of a particular tech stock and advice our customers accordingly. 
<p> The tech stocks tickers we will be working with are: MSFT, AAPL, AMZN, GOOG, BABA, FB, INTC, NVDA, CRM, PYPL, TSLA and AMD.
    
The various steps of the data pipeline are described next:

1. We will be working on the Google Cloud Platform using docker containers. The first step is always to spin up the docker containers. 
    
```
docker-compose up -d
```

2) Our driver script has some python library dependencies that requires a Python version of 3.6 or higher. So, we next describe the steps to install python 3.8 on the mids container:

- We use a bash script that automates the installation of a number of necessary packages on the mids container.

```
docker-compose exec mids sh w205-project3-shared/00_financial_api_app/startup.sh


#!/bin/bash

##update python version to 3.8

sudo apt update
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt update  
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.8

update-alternatives --install /usr/bin/python python /usr/bin/python3.8 15

sudo apt-get install python3.8-distutils
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py --force-reinstall

##Install necessary python packages

python -m  pip install flask
python -m pip install http.client
python -m pip install numpy
python -m pip install requests
python -m pip install kafka-python


##Install apache bench

apt-get update
apt-get install apache2-utils

```

- Once this script successfully runs, if we execute:

```
docker-compose exec mids python --version

Python 3.8.9
```

3) Now we are ready to launch our data pipeline. We will be reading tech stock information from the Yahoo API. 

```
docker-compose exec mids python w205-project3-shared/00_financial_api_app/server.py 
```
The ```server.py``` script is as follows:

```
#!/usr/bin/env python
import json
import time
from kafka import KafkaProducer
from flask import Flask, request, jsonify
from  stock_overview_class_one_stock import *

app = Flask(__name__)
producer = KafkaProducer(bootstrap_servers='kafka:29092')


def log_to_kafka(topic, event):
     event.update(request.headers)
     producer.send(topic, json.dumps(event).encode())

#default response
@app.route("/")
def default_response():
    default_event = {'event_type': 'default instructions'}
    log_to_kafka('event', default_event)
    return ('If you want to consult the yearly return of a stock go to the following route: /stock name\n If you want to consult a metric go to the \
            following route: /stockName/metric' )

#Check stocks
@app.route("/<stock_name>")
def testing_stock(stock_name):
    #Calling the Yahoo finance API
    stock_overview= GetStockReturns(stock_name)
    result= stock_overview.getYahooAPI()
    
    #Sending the event to kafka
    stock_request_event = {'event_type': 'check_stock_{}'.format(stock_name)}
    log_to_kafka('event', stock_request_event)

    #Final return to the user
    return result

#stock transaction
    
@app.route("/<stock_name>/<action>/<quantity>",methods = ['POST'])
def action_stock(stock_name,action,quantity):
    stock_overview = GetStockReturns(stock_name)
    if action == "buy":
        buy_price = stock_overview.get_transaction_price(stock_name,action)
        stock_transaction_event = {'event_type': '{}_{}'.format(action, stock_name),'buy_price': buy_price, 'transaction_amount' : buy_price * int(quantity), "transaction_timestamp" : time.time() * 1000}
        log_to_kafka('event', stock_transaction_event)
        return jsonify({"task": "bought_{}_{}".format(quantity,stock_name)}), 201
    
    if action == "sell":
        sell_price = stock_overview.get_transaction_price(stock_name, action)
        stock_transaction_event = {"event_type": "{}_{}".format(action, stock_name),"sell_price": sell_price, "transaction_amount" : sell_price * int(quantity),"transaction_timestamp" : time.time() * 1000}
        log_to_kafka('event', stock_transaction_event)
        return jsonify({"task": "sold_{}_{}".format(quantity, stock_name)}), 201


if __name__ == '__main__':
    app.debug=True
    app.run()

```

We now make various calls to the server:
    
- Check for a stock

```
docker-compose exec mids ab  -n 10  http://localhost:5000/GOOG
```

- Buy ceratin number of stocks

```
docker-compose exec mids ab -p project-3-atreyid/post.json -T application/json -n 10  http://localhost:5000/AMZN/buy/10
```

- Sell certain number of stocks

```
docker-compose exec mids ab -p project-3-atreyid/post.json -T application/json -n 10  http://localhost:5000/AMZN/sell/15
```

4) Withing our ```server.py``` script we have Kafka set up to log these events. We now perform a sanity check to make sure everything is running well:

```
docker-compose exec mids kafkacat -C -b kafka:29092 -t event -o beginning
    

```

