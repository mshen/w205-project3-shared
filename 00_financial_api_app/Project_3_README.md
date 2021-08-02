## W205 Project 3: Understanding User Behaviour
##### Atreyi Dasmahapatra, Andrés de la Rosa, Michelle Shen
<br>
<p> In this project we work for a company that advices customers whether to invest or not invest in certain technological stocks. Since the onset of the covid-19 pandemic, the stock market has had to deal with some drastic changes of its own. In this project we aim to analyze user behavior, in particular understand the trends of buying/selling of a particular tech stock and advise our customers accordingly.
<p>  We will be reading tech stock information from the Yahoo API.  The tech stocks tickers we will be working with are: MSFT, AAPL, AMZN, GOOG, BABA, FB, INTC, NVDA, CRM, PYPL, TSLA and AMD.
<p> We will be working on the Google Cloud Platform using docker containers.
<p> The various steps of the data pipeline are described next:

## 1. Setting up Docker

#### a. First, we spin up the docker containers:

```
docker-compose up -d
```
#### b. Then, we run a sanity check to make sure everything is up:

```
docker-compose ps
```
#### c. We can look for more specific information to ensure the containers are running.
```
docker-compose logs kafka | grep -i started
```

## 2. Installing Python 3.8 on the mids container.
Our driver script has some python library dependencies that requires a Python version of 3.6 or higher.

#### a. We use a bash script that automates the installation of a number of necessary packages on the mids container.

```
docker-compose exec mids sh w205-project3-shared/00_financial_api_app/startup.sh
```
The `startup.sh` script runs the following:

```
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

#### b. Once this script successfully runs, if we execute:

```
docker-compose exec mids python --version
```
#### we should get:
```
Python 3.8.9
```

#### c. Now we are ready to launch our server for our data pipeline.

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
        stock_transaction_event = {'event_type': '{}_{}'.format(action, stock_name),'price': buy_price, 'transaction_amount' : buy_price * int(quantity), "transaction_timestamp" : time.time() * 1000}

        log_to_kafka('stock_operation',  stock_transaction_event)
        return jsonify({"task": "bought_{}_{}".format(quantity,stock_name)}), 201

    if action == "sell":
        sell_price = stock_overview.get_transaction_price(stock_name, action)
        stock_transaction_event = {"event_type": "{}_{}".format(action, stock_name),"price": sell_price, "transaction_amount" : sell_price * int(quantity),"transaction_timestamp" : time.time() * 1000}
        log_to_kafka('stock_operation',  stock_transaction_event)
        return jsonify({"task": "sold_{}_{}".format(quantity, stock_name)}), 201


if __name__ == '__main__':
    app.debug=True
    app.run()

```

## 3. We can now make various calls to the server using another terminal:

- #### Check for a stock

```
docker-compose exec mids ab  -n 10  http://localhost:5000/GOOG
```

- #### Buy a certain number of stocks

```
docker-compose exec mids ab -p /w205/w205-project3-shared/00_financial_api_app/post.json -T application/json -n 10  http://localhost:5000/AMZN/buy/10
```

- #### Sell a certain number of stocks

```
docker-compose exec mids ab -p /w205/w205-project3-shared/00_financial_api_app/post.json -T application/json -n 10  http://localhost:5000/TSLA/sell/15
```

Within our ```server.py``` script we have Kafka set up to log these events. We now perform a some sanity checks to make sure everything is running well:

```
docker-compose exec mids kafkacat -C -b kafka:29092 -t event -o beginning
```

## 4. Automate the buying, selling and checking of stocks using a script
```
auto_generate_ab.sh
```
The auto_generate_ab.sh script is as follows:
```
#!/bin/bash
stock_tickers=('MSFT' 'AAPL' 'AMZN' 'GOOG' 'BABA' 'FB' 'INTC' 'NVDA' 'CRM' 'PYPL' 'TSLA' 'AMD')
tick_idx=`shuf -i 0-11 -n 1`

stock_rand_num=`shuf -i 1-50 -n 1`
rand_event_num=`shuf -i 1-10 -n 1`

#echo ${stock_tickers[tick_idx]}


docker-compose exec mids ab  -n $rand_event_num  http://localhost:5000/${stock_tickers[tick_idx]}
#docker-compose exec mids ab -p project-3-atreyid/post.json -T application/json -n $rand_event_num  http://localhost:5000/$stock_ticker(stock_tick)/buy/$stock_rand_num
#docker-compose exec mids ab -p project-3-atreyid/post.json -T application/json -n $rand_event_num  http://localhost:5000/$stock_tick/sell/$stock_rand_num
```

## 5. We can open new terminals to submit spark jobs; each job will run on a separate terminal.
```
docker-compose exec spark spark-submit /w205/w205-project3-shared/00_financial_api_app/stock_call_spark_job.py
```
The `stock_call_spark_job.py` runs the following:
```
#!/usr/bin/env python
"""
Extract events from kafka and write them to hdfs

"""
import json
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType



"""
We want to create two tables, one table that stores the event of calling the API,
and one event that appends the results of the API call.
"""
def stock_call_event_schema():
    """
    root
     |-- Accept: string (nullable = true)
     |-- Content-Length: string (nullable = true)
     |-- Content-Type: string (nullable = true)
     |-- Host: string (nullable = true)
     |-- User-Agent: string (nullable = true)
     |-- stock_name: string (nullable = true)
     |-- event_type: string (nullable = true)
     |-- query_timestamp: double (nullable = true)
    """
    return StructType([
        StructField("Accept", StringType(), True),
        StructField("Content-Length", StringType(), True),
        StructField("Content-Type", StringType(), True),
        StructField("Host", StringType(), True),
        StructField("User-Agent", StringType(), True),
        StructField("stock_name", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("query_timestamp", DoubleType(), True)
    ])

@udf('boolean')
def is_stock_call_event(event_as_json):
    """
    udf for filtering events
    """
    event = json.loads(event_as_json)
    if event.get("event_type").startswith("check_stock"):
        return True
    return False


def main():
    """
    main

    """
    ##We open the spark session
    spark = SparkSession \
        .builder \
        .appName("ExtractEventsJob") \
        .enableHiveSupport() \
        .getOrCreate()    


    raw_stock_call_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "stock_call") \
    .load()

    stock_calls = raw_stock_call_df \
        .filter(is_stock_call_event(raw_stock_call_df.value.cast('string'))) \
        .select(raw_stock_call_df.value.cast('string'),
                raw_stock_call_df.timestamp.cast('string'),
                from_json(raw_stock_call_df.value.cast('string'),
                          stock_call_event_schema()).alias('json')) \
        .select('json.*')

    stock_calls.printSchema()

    sink = stock_calls \
        .writeStream \
        .format("parquet") \
        .option("checkpointLocation", "/tmp/checkpoints_stock_call") \
        .option("path", "/tmp/stock_call") \
        .trigger(processingTime="20 seconds") \
        .outputMode("append") \
        .start()

    sink.awaitTermination()

#     time.sleep(20)

#     pf = spark.read.json("/tmp/stock_call")
#     pf.printSchema()
#     pf.createOrReplaceTempView("stock_call")
#     ops = spark.sql("SELECT * from stock_call")

#     pf.show(1, truncate=False)

#     #stock_calls.createOrReplaceTempView("stock_call")
#     spark.sql("drop table if exists stock_call_hive")
#     spark.sql("""
#         create table stock_call_hive
#         stored as parquet
#         location '/tmp/stock_call'
#         as
#         select * from stock_call
#     """)


if __name__ == "__main__":
    main()
```


```
docker-compose exec spark spark-submit /w205/w205-project3-shared/00_financial_api_app/stock_transaction_spark_job.py
```
The `stock_transaction_spark_job.py` runs the following:
```
#!/usr/bin/env python
"""
Extract events from kafka and write them to hdfs

"""
import json
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType



"""
We want to create two tables, one table that stores the event of calling the API,
and one event that appends the results of the API call.
"""
def stock_operation_event_schema():
    """
    root
     |-- Accept: string (nullable = true)
     |-- Content-Length: string (nullable = true)
     |-- Content-Type: string (nullable = true)
     |-- Host: string (nullable = true)
     |-- User-Agent: string (nullable = true)
     |-- price: double (nullable = true)
     |-- event_type: string (nullable = true)
     |-- transaction_amount: double (nullable = true)
     |-- transaction_timestamp: double (nullable = true)
    """
    return StructType([
        StructField("Accept", StringType(), True),
        StructField("Content-Length", StringType(), True),
        StructField("Content-Type", StringType(), True),
        StructField("Host", StringType(), True),
        StructField("User-Agent", StringType(), True),
        StructField("price", DoubleType(), True),
        StructField("event_type", StringType(), True),
        StructField("transaction_amount", DoubleType(), True),
        StructField("transaction_timestamp", DoubleType(), True)
    ])

@udf('boolean')
def is_stock_transaction_event(event_as_json):
    """
    udf for filtering events
    """
    event = json.loads(event_as_json)
    if event.get('price'):
        return True
    return False


def main():
    """
    main

    """
    ##We open the spark session
    spark = SparkSession \
        .builder \
        .appName("ExtractEventsJob") \
        .enableHiveSupport() \
        .getOrCreate()    

    ##Saving operations from user.  Topic called: stock_operation
    raw_stock_operation_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "stock_operation") \
    .load()

    stock_purchases = raw_stock_operation_df \
        .filter(is_stock_transaction_event(raw_stock_operation_df.value.cast('string'))) \
        .select(raw_stock_operation_df.value.cast('string'),
                raw_stock_operation_df.timestamp.cast('string'),
                from_json(raw_stock_operation_df.value.cast('string'),
                          stock_operation_event_schema()).alias('json')) \
        .select('json.*')

    stock_purchases.printSchema()

    sink = stock_purchases \
        .writeStream \
        .format("parquet") \
        .option("checkpointLocation", "/tmp/checkpoints_stock_operation") \
        .option("path", "/tmp/stock_operation") \
        .trigger(processingTime="20 seconds") \
        .outputMode("append") \
        .start()

#     time.sleep(20)

#     pf = spark.read.parquet("/tmp/stock_operation")
#     pf.createOrReplaceTempView("stock_operation")
#     ops = spark.sql("SELECT * from stock_operation")

#     ops.printSchema()
#     ops.show(1, truncate=False)

    sink.awaitTermination()

if __name__ == "__main__":
    main()
```
## 6. Check on another terminal that the files are being written through to /tmp

```
docker-compose exec cloudera hadoop fs -ls /tmp/stock_operation
```

```
docker-compose exec cloudera hadoop fs -ls /tmp/stock_call
```

## 7. Load data from hive and use pyspark to run some queries:

```
docker-compose exec spark pyspark
```
Queries:
```
>>> pf = spark.read.parquet("/tmp/stock_call")
>>> pf.createOrReplaceTempView("stock_call")
>>> spark.sql("SELECT * FROM stock_call").show(truncate=False)
```
```
>>> spark.sql("SELECT COUNT(stock_name) FROM stock_call GROUP BY stock_name").show(truncate=False)
```
```
>>> spark.sql("SELECT stock_name, COUNT(stock_name) as query_count FROM stock_call GROUP BY stock_name ORDER BY query_count desc LIMIT 1").show(truncate=False)
```
```
>>> spark.sql("SELECT stock_name, COUNT(stock_name) as query_count FROM stock_call GROUP BY stock_name ORDER BY query_count asc LIMIT 1").show(truncate=False)
```
```
pf = spark.read.parquet("/tmp/stock_operation")
>>> pf.createOrReplaceTempView("stock_operation")
>>> spark.sql("SELECT * FROM stock_operation").show(truncate=False)
```
```
>>> spark.sql("SELECT MAX(transaction_amount) AS max_transaction FROM stock_operation").show(truncate=False)
```