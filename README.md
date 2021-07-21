### How to run

```
cd 00_financial_api_app
python3 server.py

curl -i -H "Content-Type: application/json" -X POST  http://localhost:5000/AMZN/buy/10
curl -i -H "Content-Type: application/json" -X POST  http://localhost:5000/AMZN/sell/10

```

