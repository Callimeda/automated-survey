import concurrent.futures
import json
import logging
import os

import requests
import websocket

from automated_survey_app import AutomatedSurveyApp

ASTERISK_SERVER = os.environ.get("ASTERISK_SERVER_IP", "0.0.0.0")
ARI_USERNAME = os.environ.get("ARI_USERNAME")
ARI_PASSWORD = os.environ.get("ARI_PASSWORD")
APP_NAME = "callilexa"
DEFAULT_TIMEOUT = 3

# Asterisk ARI REST API URL
ARI_BASE_URL = f"ws://{ASTERISK_SERVER}:8088/ari/events?api_key={ARI_USERNAME}:{ARI_PASSWORD}&app={APP_NAME}"
HANDLER_SERVER = "http://localhost:3000"

EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=10)

PORT_READY = 4000
MAX_ALLOWED_PORT = 4999
CHANNEL_TO_APP_REGISTRATION = {}


# Function to handle incoming WebSocket messages (events)
def on_message(ws, message):  # pylint: disable=C0103,W0621,W0613
    decode_message = message.decode("utf8")
    json_data = json.loads(decode_message)
    if json_data["type"] == "StasisStart":
        logging.info(f"Received Stasis message: {json_data}")
        channel_name = str(json_data["channel"]["name"])
        if "PJSIP" in channel_name:
            channel_id = str(json_data["channel"]["id"])
            caller_id = str(json_data["channel"]["caller"]["number"])
            port = get_next_available_port()
            set_up_call(caller_id, channel_id, port)
            automated_survey_app = AutomatedSurveyApp(caller_id, port)
            future = EXECUTOR.submit(automated_survey_app.start)
            CHANNEL_TO_APP_REGISTRATION[channel_id] = (automated_survey_app, future)

    elif json_data["type"] == "StasisEnd":
        logging.info(f"Received message: {json_data}")
        channel_name = str(json_data["channel"]["name"])
        if "PJSIP" in channel_name:
            channel_id = str(json_data["channel"]["id"])
            automated_survey_app, future = CHANNEL_TO_APP_REGISTRATION.pop(channel_id)
            automated_survey_app.stop()
            future.result()


def set_up_call(caller_id: str, channel_id: str, port: int) -> None:
    data = {
        "caller_id": str(caller_id),
        "channel_id": str(channel_id),
        "port": str(port),
    }
    json_data = json.dumps(data)
    headers = {"Content-Type": "application/json"}
    requests.post(
        f"{HANDLER_SERVER}/set_up_call",
        json=json_data,
        headers=headers,
        timeout=DEFAULT_TIMEOUT,
    )


def get_next_available_port() -> int:
    global PORT_READY
    port = PORT_READY
    if port == 4999:
        PORT_READY = 3999
    PORT_READY += 1
    return port


# Function to handle WebSocket error events
def on_error(ws, error):  # pylint: disable=W0613,C0103,W0621
    logging.info(f"Error: {error}")


# Function to handle WebSocket close events
def on_close(ws, close_status_code, close_msg):  # pylint: disable=C0103,W0621,W0613
    logging.info("Asterisk WebSocket connection closed")
    if close_status_code or close_msg:
        logging.info("close status code: " + str(close_status_code))
        logging.info("close message: " + str(close_msg))


if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        ARI_BASE_URL, on_message=on_message, on_error=on_error, on_close=on_close
    )
    ws.run_forever(
        skip_utf8_validation=True,
    )
