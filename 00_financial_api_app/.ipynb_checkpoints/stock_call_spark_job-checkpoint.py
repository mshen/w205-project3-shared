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
