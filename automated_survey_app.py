import argparse
import logging
import socket

MY_IP = "0.0.0.0"


class AutomatedSurveyApp:  # pylint: disable=R0902
    def __init__(self, caller_id, port):
        self.caller_id = caller_id
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        self.sock.bind((MY_IP, int(self.port)))
        logging.info(f"Listening for packets on {MY_IP}:{self.port}")

    def stop(self):
        return


def main(caller_id: str, port: str) -> None:
    try:
        automated_survey_app = AutomatedSurveyApp(caller_id, port)
        automated_survey_app.start()
    except Exception as e:  # pylint: disable=W0718
        logging.info(f"An error occurred: {str(e)}")
        automated_survey_app.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process the port to open.")
    parser.add_argument("caller_id", type=str, help="The caller id")
    parser.add_argument("port", type=str, help="The port on which the program runs")
    args = parser.parse_args()
    main(args.caller_id, args.port)
