# automated-survey

VR system that collects customer satisfaction feedback after a support call. This is a scalable, fault-tolerant system 
that can handle automated surveys over the phone.

## Run events listener
python events_listener.py

## Run Asterik API (ARI) wrapper
flask --app golden_friend/app.py run --port 3000
