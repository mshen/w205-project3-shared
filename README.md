## W205 Project 3: Understanding User Behaviour
##### Atreyi Dasmahapatra, Andrés de la Rosa, Michelle Shen
<br>
<p> In this project we work for a company that advises customers whether to invest or not invest in certain technological stocks. Since the onset of the COVID-19 pandemic, the stock market has had to deal with some drastic changes of its own. In this project we aim to analyze user behavior, in particular understand the trends of buying/selling of a particular tech stock and monitor stock tradings over a certain period of time.
<p>  We will be reading tech stock information from the Yahoo API.  The tech stocks tickers we will be working with are: MSFT, AAPL, AMZN, GOOG, BABA, FB, INTC, NVDA, CRM, PYPL, TSLA and AMD.
<p> We will be working on the Google Cloud Platform using Docker containers.
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
#### c. We can look for more specific information to ensure the containers are running:
```
docker-compose logs kafka | grep -i started
```

## 2. Installing Python 3.8 on the mids container.
Our driver script has some Python library dependencies that requires a Python version of 3.6 or higher.

#### a. We use a bash script that automates the installation of a number of necessary packages on the mids container.

```
docker-compose exec mids sh w205-project3-shared/00_financial_api_app/startup.sh
```
The `startup.sh` script runs the following:

```
#!/bin/bash

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

python -m  pip install flask
python -m pip install http.client
python -m pip install numpy
python -m pip install requests
python -m pip install kafka-python


#install apache bench
apt-get update
apt-get install apache2-utils

```

#### b. Once this script successfully runs, if we execute:

```
docker-compose exec mids python --version
```
#### we should get `Python 3.8.9` as the current version.

#### c. Now we are ready to launch our server for our data pipeline using the following command.

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

```

## 3. We can now make various calls to the server using another terminal. Note that the following steps are examples to show what is possible, but we wrote these into the script that is executed in step 4 and therefore do not execute these in our pipeline.

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

## 4. Automate the buying, selling and checking of stocks using a script using Apache Bench.
<p> We next run our script that autogenerates various types of calls:
```
./auto_generate_ab.sh
```
The auto_generate_ab.sh script is as follows:

```
#!/bin/bash
stock_tickers=('MSFT' 'AAPL' 'AMZN' 'GOOG' 'BABA' 'FB' 'INTC' 'NVDA' 'CRM' 'PYPL' 'TSLA' 'AMD')
tick_idx_1=`shuf -i 0-11 -n 1`
tick_idx_2=`shuf -i 0-11 -n 1`
tick_idx_3=`shuf -i 0-11 -n 1`

stock_rand_num=`shuf -i 1-50 -n 1`
rand_event_num=`shuf -i 1-3 -n 1`

#echo ${stock_tickers[tick_idx]}


docker-compose exec mids ab  -n $rand_event_num  http://localhost:5000/${stock_tickers[tick_idx_1]}

docker-compose exec mids ab -p /w205/w205-project3-shared/00_financial_api_app/post.json -T application/json -n $rand_event_num  http://localhost:5000/${stock_tickers[tick_idx_2]}/buy/$stock_rand_num

docker-compose exec mids ab -p /w205/w205-project3-shared/00_financial_api_app/post.json -T application/json -n $rand_event_num  http://localhost:5000/${stock_tickers[tick_idx_3]}/sell/$stock_rand_num
```

 
## 5. We open 3 new terminals to submit spark jobs; each of the following jobs will run on a separate terminal.
#### a. Terminal 1: `stock_call_spark_job.py`
In the first terminal, we run this spark job to create dataframs from the kafka topic stock calls:
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
    .option("startingOffsets","earliest")\
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
    
    

if __name__ == "__main__":
    main()
```

#### b. Terminal 2: `stock_transaction_spark_job.py`
In the second terminal, we run the following spark job to create spark data frames for the Kafka topic for stock transactions:

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
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType



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
     |-- quantity: int (nullable = true)
     |-- stock_name: string (nullable = true)
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
        StructField("stock_name", StringType(), True),
        StructField("quantity", IntegerType(), True),
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
    .option("startingOffsets","earliest")\
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

    
    sink.awaitTermination()

if __name__ == "__main__":
    main()
```

#### c. Terminal 3: `create_hive_table_spark_job.py`
In the third terminal, we run a spark job to create tables from hive.

```
docker-compose exec spark spark-submit /w205/w205-project3-shared/00_financial_api_app/create_hive_table_spark_job.py
```

The spark job `create_hive_table_spark_job.py` runs the following:

```
#!/usr/bin/env python

import json
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

def main():
    """
    main

    """
    while True:
        # We open the spark session
        spark = SparkSession \
            .builder \
            .appName("CreateHiveTableJob") \
            .enableHiveSupport() \
            .getOrCreate()


        spark.sql("drop table if exists stock_call_hive")
        spark.sql("""
            create external table stock_call_hive (accept STRING, content_length STRING, content_type STRING, host STRING, user_agent STRING, stock_name STRING, event_type STRING, query_imestamp DOUBLE)
            stored as parquet
            location '/tmp/stock_call'
            TBLPROPERTIES ("parquet.compress" = "SNAPPY")
        """)
    
        spark.sql("drop table if exists stock_operation_hive")
        spark.sql("""
            create external table stock_operation_hive (accept STRING, content_length STRING, content_type STRING, host STRING, user_agent STRING, stock_name STRING, quantity INT, price DOUBLE, event_type STRING, transaction_amount DOUBLE, transaction_timestamp DOUBLE)
            stored as parquet
            location '/tmp/stock_operation'
            TBLPROPERTIES ("parquet.compress" = "SNAPPY")
        """)
        time.sleep(30)

if __name__ == "__main__":
    main()
```


## 6. Check on a new terminal that the files are being written through to /tmp

```
docker-compose exec cloudera hadoop fs -ls /tmp/stock_operation
```

```
docker-compose exec cloudera hadoop fs -ls /tmp/stock_call
```

## 7. Load the data from hive and using presto run some queries:
Use presto to access the tables:
```
docker-compose exec presto presto --server presto:8080 --catalog hive --schema default
```
The following command shows the tables. There are two tables, `stock_call_hive` and `stock_operation_hive`.
```
presto:default> show tables;
```
## 8. Make queries from each table.
#### a. From the `stock_call_hive` table, we query the most checked stock.
```
presto:default> 
SELECT stock_name, COUNT(stock_name) AS call_frequency \
FROM stock_call_hive \
GROUP BY stock_name \
ORDER BY call_frequency desc \
LIMIT 1;

<p> An example of the output is shown here:
stock_name  | call_frequency 
------------+----------------
 TSLA       |        35 
(1 row)
```
We can run several more similar queries to create reports and analyze results.

#### b. From the `stock_operation_hive` table, we run queries to answer the following:

What were the most purchased stocks and average price of purchase?
```
presto:default> presto:default> WITH purchases AS (SELECT * FROM stock_operation_hive WHERE event_type LIKE '%buy%') SELECT stock_name, SUM(quantity) AS total_quantity_purchased, AVG(price/quantity) AS avg_price_per_stock FROM purchases GROUP BY stock_name ORDER BY total_quantity_purchased DESC LIMIT 5;
```
What were the least purchased stocks and average price of purchase?
```
presto:default> presto:default> WITH purchases AS (SELECT * FROM stock_operation_hive WHERE event_type LIKE '%buy%') SELECT stock_name, SUM(quantity) AS total_quantity_purchased, AVG(price/quantity) AS avg_price_per_stock FROM purchases GROUP BY stock_name ORDER BY total_quantity_purchased ASC LIMIT 5;

```
What were the most sold stocks and average price of sale?
```
presto:default> presto:default> WITH sales AS (SELECT * FROM stock_operation_hive WHERE event_type LIKE '%sell%') SELECT stock_name, SUM(quantity) AS total_quantity_sold, AVG(price/quantity) AS avg_price_per_stock FROM sales GROUP BY stock_name ORDER BY total_quantity_sold DESC LIMIT 5;
```
What were the least sold stocks and average price of sale?
```
presto:default> presto:default> WITH sales AS (SELECT * FROM stock_operation_hive WHERE event_type LIKE '%sell%') SELECT stock_name, SUM(quantity) AS total_quantity_sold, AVG(price/quantity) AS avg_price_per_stock FROM sales GROUP BY stock_name ORDER BY total_quantity_sold ASC LIMIT 5;
```
What was the highest price a stock sold for?
```
WITH sales AS (SELECT * FROM stock_operation_hive WHERE event_type LIKE '%sell%') SELECT stock_name, price/quantity AS price_per_stock FROM sales ORDER BY price_per_stock DESC LIMIT 5;
```
What was the lowest price a stock sold for?
```
WITH sales AS (SELECT * FROM stock_operation_hive WHERE event_type LIKE '%sell%') SELECT stock_name, price/quantity AS price_per_stock FROM sales ORDER BY price_per_stock ASC LIMIT 5;
```
What was the highest price a stock was bought for?
```
WITH purchases AS (SELECT * FROM stock_operation_hive WHERE event_type LIKE '%buy%') SELECT stock_name, price/quantity AS price_per_stock FROM purchases ORDER BY price_per_stock DESC LIMIT 5;
```
What was the lowest price a stock was bought for?
```
WITH purchases AS (SELECT * FROM stock_operation_hive WHERE event_type LIKE '%buy%') SELECT stock_name, price/quantity AS price_per_stock FROM purchases ORDER BY ASC price_per_stock ASC LIMIT 5;

```
     



