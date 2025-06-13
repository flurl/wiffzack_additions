from typing import Any, LiteralString, NoReturn
import bluetooth
import requests
import time
import threading
import logging


# --- Configuration ---
ESP32_MAC_ADDRESS: LiteralString = "08:B6:1F:28:53:8E"
BLUETOOTH_PORT: int = 1  # Standard SPP port
API_URL: LiteralString = "http://192.168.3.50:5000/api/storage_article_groups/{storage_id}"
MONITORING_INTERVAL_SECONDS: int = 30
BT_ARTICLES_FOUND_FLAG: bytes = bytes([1])
BT_NO_ARTICLES_FOUND_FLAG: bytes = bytes(1)
CONFIG_URL: LiteralString = "http://192.168.3.50:5000/api/get_config"
config: dict[str, Any] | None = None

# --- Setup Logging ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
)


def load_config() -> None:
    """
    Loads configuration from the CONFIG_URL and stores it in the global CONFIG variable.
    """
    global config  # Declare CONFIG as global to modify it
    headers: dict[str, str] = {
        'Accept': 'application/json'
    }
    logging.info(f"Attempting to load configuration from {CONFIG_URL}")
    try:
        response: requests.Response = requests.get(
            CONFIG_URL, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

        api_response: Any = response.json()

        if api_response.get("success") and "config" in api_response:
            config = api_response["config"]
            logging.info(f"Successfully loaded configuration: {config}")
        else:
            logging.error(
                f"Failed to load configuration. 'success' was not true or 'config' key missing in response from {CONFIG_URL}. Response: {api_response}")
            config = None  # Ensure CONFIG is None if loading fails

    except Exception as e:
        logging.error(
            f"An unexpected error occurred while loading configuration from {CONFIG_URL}: {e}", exc_info=True)
        config = None


def check_articles_available(url: str) -> bool:
    """
    Checks the API for available articles.
    Expects a JSON response like: {"success": true, "data": [...]}.
    Returns True if articles are found (data list is not empty), False otherwise.
    """
    headers: dict[str, str] = {
        'Accept': 'application/json'
    }
    try:
        response: requests.Response = requests.get(
            url, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

        api_response: Any = response.json()

        if api_response.get("success") and isinstance(api_response.get("data"), list) and api_response["data"]:
            logging.info(
                f"Articles found at {url}. Data: {api_response['data']}")
            return True
        else:
            logging.debug(
                f"No articles found or 'data' field empty/missing in response from {url}.")
            return False

    except Exception as e:
        logging.error(
            f"An unexpected error occurred while checking API {url}: {e}")
        return False


def send_bluetooth_notification(mac_address: str, port: int, message: bytes):
    """
    Connects to the ESP32 via Bluetooth and sends a notification message.
    """
    sock = None
    try:
        logging.debug(
            f"Attempting to connect to Bluetooth device {mac_address} on port {port}")
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((mac_address, port))  # type: ignore
        logging.info(f"Connected to ESP32 at {mac_address}")

        sock.send(message)  # type: ignore
        logging.info(f"Sent notification data: {message!r}")

        try:
            sock.settimeout(5.0)  # type: ignore
            data_received = sock.recv(1024)  # type: ignore
            if data_received:
                logging.info(
                    f"Received from ESP32: {data_received.decode(errors='ignore')}")  # type: ignore
        except bluetooth.btcommon.BluetoothError as e:  # type: ignore
            if "timed out" in str(e).lower():  # type: ignore
                logging.debug(
                    "Timeout waiting for response from ESP32, assuming send was successful.")
            else:
                logging.warning(f"Bluetooth error while receiving data: {e}")

    except bluetooth.btcommon.BluetoothError as e:  # type: ignore
        logging.error(f"Bluetooth Error: {e}")
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during Bluetooth communication: {e}")
    finally:
        if sock:
            sock.close()  # type: ignore
            logging.info("Bluetooth connection closed.")


def monitoring_loop() -> NoReturn:
    """
    Main loop for the monitoring thread.
    Periodically checks for articles and sends a Bluetooth notification if found.
    """
    logging.info("Monitoring thread started. Will check API every %s seconds.",
                 MONITORING_INTERVAL_SECONDS)
    while True:
        try:
            assert config is not None
            articles_found: bool = False
            for terminal in config:
                if not config[terminal].get("request_storage_id"):
                    logging.info(
                        f"No request storage defined for terminal {terminal}. Skipping.")
                    continue
                url: str = API_URL.format(
                    storage_id=config[terminal]["request_storage_id"])

                logging.debug(f"Checking for articles at {url}")
                if check_articles_available(url):
                    logging.info(
                        "Articles found.")
                    articles_found = True
                else:
                    logging.debug(
                        "No articles currently available or error during check.")

            if articles_found:
                logging.info(
                    "Articles available. Attempting to send Bluetooth notification.")
                send_bluetooth_notification(
                    ESP32_MAC_ADDRESS, BLUETOOTH_PORT, BT_ARTICLES_FOUND_FLAG)
            else:
                send_bluetooth_notification(
                    ESP32_MAC_ADDRESS, BLUETOOTH_PORT, BT_NO_ARTICLES_FOUND_FLAG)

            logging.debug(
                f"Waiting for {MONITORING_INTERVAL_SECONDS} seconds before next check.")
            time.sleep(MONITORING_INTERVAL_SECONDS)
        except Exception as e:
            logging.error(f"Error in monitoring loop: {e}", exc_info=True)
            # Avoid rapid-fire loops on persistent errors
            time.sleep(MONITORING_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.info("Starting Bluetooth Storage Watcher.")

    load_config()
    # You can add a check here if CONFIG is None and decide if the program should continue
    if config is None:
        logging.warning(
            "Configuration could not be loaded. Proceeding with default/no specific config values.")
    # else:
    #     # Example: Potentially use CONFIG values to override defaults
    #     ESP32_MAC_ADDRESS = CONFIG.get("bluetooth_beacon", {}).get("mac_address", ESP32_MAC_ADDRESS)
    #     # ... and so on for other configurable parameters

    # Create and start the monitoring thread
    # daemon=True ensures the thread exits when the main program exits
    monitor_thread = threading.Thread(
        target=monitoring_loop, name="APIMonitorThread", daemon=True)
    monitor_thread.start()

    logging.info(
        "Monitoring thread dispatched. Main thread will wait. Press Ctrl+C to exit.")

    try:
        # Keep the main thread alive to allow the daemon thread to run.
        # monitor_thread.join() would also work if you want the main thread
        # to explicitly wait for the monitor_thread to finish (e.g., if it had a natural end).
        while True:
            time.sleep(1)  # Keep main thread alive, sleep to reduce CPU usage
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Shutting down...")
    finally:
        logging.info("Bluetooth Storage Watcher finished.")
