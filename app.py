import json
import logging
import os
from typing import Any

import requests
from flask import Flask, jsonify, request
from requests import Response

app = Flask(__name__)

ASTERISK_SERVER = os.environ.get("ASTERISK_SERVER_IP", "0.0.0.0")
ARI_BASE_URL = f"http://{ASTERISK_SERVER}:8088/ari"
ARI_USERNAME = os.environ.get("ARI_USERNAME", "")
ARI_PASSWORD = os.environ.get("ARI_PASSWORD", "")
EXTERNAL_MEDIA_SERVER = "0.0.0.0"
MAX_RETRIES = 10
RETRY_DELAY = 1
DEFAULT_TIMEOUT = 10


@app.route("/set_up_call", methods=["POST"])
def set_up_call():
    if request.is_json:
        # Extract JSON data from the request
        json_data = json.loads(request.get_json())
        logging.info(f"Received a request to set up a call: {json_data}")

        originating_channel_id = json_data["channel_id"]
        port = json_data["port"]

        answer_channel(originating_channel_id)
        response = forward_to_processor(port)
        new_created_channel_id = response.json()["id"]
        logging.info(f"Created new channel: {new_created_channel_id}")
        response = create_mixing_bridge()
        new_created_bridge_id = response.json()["id"]
        add_channels_to_bridge(
            new_created_bridge_id, [originating_channel_id, new_created_channel_id]
        )
        get_bridge_info(new_created_bridge_id)

        # Return a response (optional)
        return jsonify({"message": "JSON data processed successfully"})

    # If the request does not contain JSON data, return an error response
    return jsonify({"error": "Request does not contain JSON data"}), 400


def answer_channel(channel_id: str) -> Any:
    endpoint = f"/channels/{channel_id}/answer"
    response = ari_post_request(endpoint, {})
    response.raise_for_status()
    logging.info(f"The response for {endpoint} was: {response}")
    return response


def forward_to_processor(port: str) -> Any:
    endpoint = (
        "/channels/externalMedia?app=callilexa"
        f"&external_host={EXTERNAL_MEDIA_SERVER}:{port}&format=ulaw&connection_type=client&direction=both"
    )
    response = ari_post_request(endpoint, {})
    response.raise_for_status()
    logging.info(f"The response for {endpoint} was: {response} / {response.json()}")
    return response


def create_mixing_bridge() -> Any:
    endpoint = "/bridges?type=mixing"
    response = ari_post_request(endpoint, {})
    response.raise_for_status()
    logging.info(f"The response for {endpoint} was: {response} / {response.json()}")
    return response


def add_channels_to_bridge(bridge_id: str, channels: list[str]) -> None:
    for channel in channels:
        endpoint = f"/bridges/{bridge_id}/addChannel?channel={channel}"
        response = ari_post_request(endpoint, {})
        response.raise_for_status()
        logging.info(f"The response for {endpoint} was: {response}")


def get_bridge_info(bridge_id: str) -> None:
    endpoint = f"/bridges/{bridge_id}"
    response = ari_get_request(endpoint)
    response.raise_for_status()
    logging.info(f"The response for {endpoint} was: {response} / {response.json()}")


# Function to perform a GET request to the ARI server
def ari_get_request(endpoint):
    url = f"{ARI_BASE_URL}{endpoint}"
    logging.info(f"GET request received: {url}")
    return send_request("GET", url, ari_auth=(ARI_USERNAME, ARI_PASSWORD))


def ari_post_request(endpoint, _data):
    url = f"{ARI_BASE_URL}{endpoint}"
    logging.info(f"POST request received: {url}")
    return send_request("POST", url, ari_auth=(ARI_USERNAME, ARI_PASSWORD))


# Function to perform a DELETE request to the ARI server
def ari_delete_request(endpoint):
    url = f"{ARI_BASE_URL}{endpoint}"
    logging.info(f"DELETE request received: {url}")
    return send_request("DELETE", url, ari_auth=(ARI_USERNAME, ARI_PASSWORD))


def send_request(
    method: str,
    url: str,
    ari_auth: tuple[str, str],
    timeout: int = DEFAULT_TIMEOUT,
) -> Response:
    return requests.request(method, url, auth=ari_auth, timeout=timeout)


if __name__ == "__main__":
    app.run(debug=True)
