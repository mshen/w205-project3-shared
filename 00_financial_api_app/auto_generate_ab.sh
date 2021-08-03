#!/bin/bash
stock_tickers=('MSFT' 'AAPL' 'AMZN' 'GOOG' 'BABA' 'FB' 'INTC' 'NVDA' 'CRM' 'PYPL' 'TSLA' 'AMD')
tick_idx=`shuf -i 0-11 -n 1`

stock_rand_num=`shuf -i 1-50 -n 1`
rand_event_num=`shuf -i 1-10 -n 1`

#echo ${stock_tickers[tick_idx]}


docker-compose exec mids ab  -n $rand_event_num  http://localhost:5000/${stock_tickers[tick_idx]}

docker-compose exec mids ab -p project-3-atreyid/post.json -T application/json -n $rand_event_num  http://localhost:5000/$stock_ticker(stock_tick)/buy/$stock_rand_num

docker-compose exec mids ab -p project-3-atreyid/post.json -T application/json -n $rand_event_num  http://localhost:5000/$stock_tick/sell/$stock_rand_num


