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

