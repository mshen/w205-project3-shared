

#!/usr/bin/env python
import json
#from kafka import KafkaProducer
from flask import Flask, request

app = Flask(__name__)
#producer = KafkaProducer(bootstrap_servers='kafka:29092')

##This is for the use of kafka in the container
# =============================================================================
# def log_to_kafka(topic, event):
#     event.update(request.headers)
#     producer.send(topic, json.dumps(event).encode())
# 
# =============================================================================

@app.route("/")
def default_response():
    default_event = {'event_type': 'default'}
    #log_to_kafka('events', default_event)
    return "This is the default response!\n"


@app.route("/purchase_a_sword")
def purchase_a_sword():
    purchase_sword_event = {'event_type': 'purchase_sword'}
    #log_to_kafka('events', purchase_sword_event)
    return "Sword Purchased!\n"



##This is a very important thing to have since it will run the application after you pass it in the CLI, or 
# as I prefer the ANACONDA PROMPT HAHAHA
if __name__ == '__main__':
    app.debug=True
    app.run()