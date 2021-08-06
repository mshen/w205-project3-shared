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
