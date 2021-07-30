#!/usr/bin/env python
"""Extract events from kafka and write them to hdfs
"""
import json
from pyspark.sql import SparkSession, Row
#from pyspark.sql.functions import udf


"""
We want to create two tables, one table that stores the event of calling the API, 
and one event that appends the results of the API call. 
"""

from pyspark import SparkContext, SparkConf
from pyspark.conf import SparkConf
from pyspark.sql import SparkSession, HiveContext

def main():
    """main
    """
    ##We open the spark session
#     spark = SparkSession \
#         .builder.master("yarn") \
#         .appName("ExtractEventsJob") \
#         .enableHiveSupport() \
#         .getOrCreate()
    
    spark = SparkSession.builder.appName('example-pyspark-read-and-write-from-hive').config("hive.metastore.uris", "thrift://localhost:9083", conf=SparkConf()).enableHiveSupport().getOrCreate()
    
    ##Stock call event from user- Topic: stock_call
#     raw_events = spark \
#     .read \
#     .format("kafka") \
#     .option("kafka.bootstrap.servers", "kafka:29092") \
#     .option("subscribe", "stock_call") \
#     .option("startingOffsets", "earliest") \
#     .option("endingOffsets", "latest") \
#     .load()
    

#     stock_events  = raw_events \
#         .select(raw_events.value.cast('string').alias('raw'),
#                 raw_events.timestamp.cast('string')) 
                
#     extracted_stock_events = stock_events \
#         .rdd \
#         .map(lambda r: Row(timestamp=r.timestamp, **json.loads(r.raw))) \
#         .toDF()
#     extracted_stock_events.printSchema()
#     extracted_stock_events.show()


#     #We register our tables to hive to then analyze the data that we have
#     extracted_stock_events.registerTempTable("extracted_stock_events")

#     spark.sql("""
#         create external table extracted_stock_events
#         stored as parquet
#         location '/tmp/extracted_stock_events'
#         as
#         select * from extracted_stock_events
#     """)
    
#     ##Data gathered from user- Topic: stock_results
#     raw_user_results = spark \
#     .read \
#     .format("kafka") \
#     .option("kafka.bootstrap.servers", "kafka:29092") \
#     .option("subscribe", "stock_results") \
#     .option("startingOffsets", "earliest") \
#     .option("endingOffsets", "latest") \
#     .load()
    
#     raw_user_results.cache()
#     raw_user_results = raw_user_results.select(raw_user_results.value.cast('string'))
#     raw_user_results = raw_user_results.rdd.map(lambda x: json.loads(x.value)).toDF()
#     raw_user_results.printSchema()
    
#     raw_user_results.registerTempTable('extracted_user_results')

#     spark.sql("""
#         create external table extracted_user_results
#         stored as parquet
#         location '/tmp/extracted_user_results'
#         as
#         select * from extracted_user_results
#     """)
    
#     ##Saving operations from user.  Topic called: stock_operation
#     raw_stock_operations = spark \
#     .read \
#     .format("kafka") \
#     .option("kafka.bootstrap.servers", "kafka:29092") \
#     .option("subscribe", "stock_operation") \
#     .option("startingOffsets", "earliest") \
#     .option("endingOffsets", "latest") \
#     .load()

#     raw_stock_operations.cache()
#     raw_stock_operations = raw_stock_operations.select(raw_stock_operations.value.cast('string'))
#     stock_operations = raw_stock_operations.rdd.map(lambda x: json.loads(x.value)).toDF()
#     stock_operations.printSchema()

#     stock_operations.registerTempTable('stock_operations')

#     spark.sql("""
#         create external table stock_operations
#         stored as parquet
#         location '/tmp/stock_operations'
#         as
#         select * from stock_operations
#     """)
    
if __name__ == "__main__":
    main()
