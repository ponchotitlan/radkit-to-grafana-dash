import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    """
    Main function to execute all the API endpoint calls to your FastAPI container.
    Your calls will be executed whenever the cron job is triggered.
    The `requests` library is imported for this purpose.
    """
    pass

MAX_THREAD_WORKERS = 10
DEVICES_LIST_URL = "http://radkit-to-grafana-fastapi-middleware:8000/devices"
DEVICE_INTERFACE_TRAFFIC_URL = "http://radkit-to-grafana-fastapi-middleware:8000/device/__DEVICE__/interfaces/traffic"

def get_device_names() -> [str]: # type: ignore
    """
    Retrieves a list of all device names from the middleware service.
    Raises an exeption if the request fails.
    """
    response = requests.get(DEVICES_LIST_URL)
    response.raise_for_status()
    devices = response.json()
    return [device['name'] for device in devices]

def worker_interface_traffic( device_name:str ) -> dict:
    """
    Fetches interface traffic data for a specified device.
    Raises an exception if the request fails.
    """
    response = requests.get(DEVICE_INTERFACE_TRAFFIC_URL.replace("__DEVICE__", device_name))
    response.raise_for_status()
    return response.json()

def execute_interface_traffic():
    """
    Gets all device names and fetches their interface traffic data concurrently.
    Handles exceptions for individual device during the requests.
    """
    # Extraction of all device names
    device_names = get_device_names()
    with ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
        future_to_device = {executor.submit(worker_interface_traffic, device_name): device_name for device_name in device_names}
        for future in as_completed(future_to_device):
            device_name = future_to_device[future]
            try:
                result = future.result()
                print(f"Device: {device_name}, Traffic Data: {result}")
            except Exception as e:
                print(f"Error fetching data for {device_name}: {e}")

if __name__ == "__main__":
    execute_interface_traffic()
