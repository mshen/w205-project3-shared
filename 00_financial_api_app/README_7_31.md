Project 3: W205: Notes 7/31/2021

docker-compose up -d
docker-compose ps
docker-compose exec mids sh w205-project3-shared/00_financial_api_app/startup.sh
docker-compose exec mids python w205-project3-shared/00_financial_api_app/server.py

#On another terminal create new events
docker-compose exec mids ab  -n 10  http://localhost:5000/GOOG
docker-compose exec mids ab -p /w205/w205-project3-shared/00_financial_api_app/post.json -T application/json -n 10  http://localhost:5000/AMZN/buy/10
docker-compose exec mids ab -p /w205/w205-project3-shared/00_financial_api_app/post.json -T application/json -n 10  http://localhost:5000/TSLA/sell/15

#Open a new terminals to submit spark jobs; each job will run on a separate terminal 
docker-compose exec spark spark-submit /w205/w205-project3-shared/00_financial_api_app/stock_call_spark_job.py
docker-compose exec spark spark-submit /w205/w205-project3-shared/00_financial_api_app/stock_transaction_spark_job.py

#You can check on another terminal if the files are being written through to /tmp
docker-compose exec cloudera hadoop fs -ls /tmp/stock_operation
docker-compose exec cloudera hadoop fs -ls /tmp/stock_call

# Running queries at the pyspark prompt for the streamed data
(base) jupyter@w204-scratch:~/w205/w205-project3-shared/00_financial_api_app$ docker-compose exec spark pyspark


>>> pf = spark.read.parquet("/tmp/stock_call")
>>> pf.createOrReplaceTempView("stock_call")
>>> spark.sql("SELECT * FROM stock_call").show(truncate=False)
+------+--------------+------------+--------------+---------------+----------+----------------+---------------------+
|Accept|Content-Length|Content-Type|Host          |User-Agent     |stock_name|event_type      |query_timestamp      |
+------+--------------+------------+--------------+---------------+----------+----------------+---------------------+
|*/*   |null          |null        |localhost:5000|ApacheBench/2.3|TSLA      |check_stock_TSLA|1.6277911073197932E12|
|*/*   |null          |null        |localhost:5000|ApacheBench/2.3|TSLA      |check_stock_TSLA|1.6277911082096335E12|
|*/*   |null          |null        |localhost:5000|ApacheBench/2.3|TSLA      |check_stock_TSLA|1.6277911091398552E12|
|*/*   |null          |null        |localhost:5000|ApacheBench/2.3|TSLA      |check_stock_TSLA|1.6277911100659517E12|
|*/*   |null          |null        |localhost:5000|ApacheBench/2.3|AMZN      |check_stock_AMZN|1.6277910609252664E12|
|*/*   |null          |null        |localhost:5000|ApacheBench/2.3|AMZN      |check_stock_AMZN|1.6277910618273489E12|
|*/*   |null          |null        |localhost:5000|ApacheBench/2.3|GOOG      |check_stock_GOOG|1.627791091021184E12 |
|*/*   |null          |null        |localhost:5000|ApacheBench/2.3|GOOG      |check_stock_GOOG|1.627791092392745E12 |
|*/*   |null          |null        |localhost:5000|ApacheBench/2.3|MSFT      |check_stock_MSFT|1.6277911234647632E12|
+------+--------------+------------+--------------+---------------+----------+----------------+---------------------+

>>> spark.sql("SELECT COUNT(stock_name) FROM stock_call GROUP BY stock_name").show(truncate=False)
+-----------------+                                                             
|count(stock_name)|
+-----------------+
|4                |
|2                |
|2                |
|1                |
+-----------------+

>>> spark.sql("SELECT stock_name, COUNT(stock_name) as query_count FROM stock_call GROUP BY stock_name ORDER BY query_count desc LIMIT 1").show(truncate=False)
+----------+-----------+                                                        
|stock_name|query_count|
+----------+-----------+
|TSLA      |4          |
+----------+-----------+

>>> spark.sql("SELECT stock_name, COUNT(stock_name) as query_count FROM stock_call GROUP BY stock_name ORDER BY query_count asc LIMIT 1").show(truncate=False)
+----------+-----------+                                                        
|stock_name|query_count|
+----------+-----------+
|MSFT      |1          |
+----------+-----------+

pf = spark.read.parquet("/tmp/stock_operation")
>>> pf.createOrReplaceTempView("stock_operation")
>>> spark.sql("SELECT * FROM stock_operation").show(truncate=False)
+------+--------------+----------------+--------------+---------------+-----------------+----------+------------------+---------------------+
|Accept|Content-Length|Content-Type    |Host          |User-Agent     |price            |event_type|transaction_amount|transaction_timestamp|
+------+--------------+----------------+--------------+---------------+-----------------+----------+------------------+---------------------+
|*/*   |0             |application/json|localhost:5000|ApacheBench/2.3|687.2000122070312|sell_TSLA |687200.0122070312 |1.6277916154072905E12|
|*/*   |0             |application/json|localhost:5000|ApacheBench/2.3|687.2000122070312|sell_TSLA |687200.0122070312 |1.6277916163112913E12|
|*/*   |0             |application/json|localhost:5000|ApacheBench/2.3|2704.419921875   |sell_GOOG |270441.9921875    |1.6277916392756277E12|
|*/*   |0             |application/json|localhost:5000|ApacheBench/2.3|2704.419921875   |sell_GOOG |270441.9921875    |1.6277916406500693E12|
|*/*   |0             |application/json|localhost:5000|ApacheBench/2.3|3347.949951171875|buy_AMZN  |33479.49951171875 |1.6277915764409517E12|
|*/*   |0             |application/json|localhost:5000|ApacheBench/2.3|3347.949951171875|buy_AMZN  |33479.49951171875 |1.6277915778240837E12|
|*/*   |0             |application/json|localhost:5000|ApacheBench/2.3|2710.219970703125|buy_GOOG  |27102.19970703125 |1.6277915885463035E12|
|*/*   |0             |application/json|localhost:5000|ApacheBench/2.3|2710.219970703125|buy_GOOG  |27102.19970703125 |1.627791589555333E12 |
+------+--------------+----------------+--------------+---------------+-----------------+----------+------------------+---------------------

spark.sql("SELECT MAX(transaction_amount) AS max_transaction FROM stock_operation").show(truncate=False)+-----------------+
|max_transaction  |
+-----------------+
|687200.0122070312|
+-----------------+

Things to be done:

- In server.py stock_operation event should suppy the stock_name and stock_quantity. This will help us write simpler queries
- Write a job which will run the queries (that we do here manually on the pyspark prompt) as a spark job
- Add some more queries
    - What is the most traded stock (by quantity) ?
    - Etc. etc.