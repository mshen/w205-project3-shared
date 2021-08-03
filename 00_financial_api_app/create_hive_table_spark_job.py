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


