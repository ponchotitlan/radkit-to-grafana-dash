import sys
from typing import Any
from contextlib import asynccontextmanager
from fastapi import FastAPI
from radkit_client.sync import Client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import radkit_genie
import yaml
import json
import uvicorn
import os

INFLUXDB_URL = "http://influxdb:8086"
INFLUXDB_TOKEN = "radkit-to-grafana"
INFLUXDB_ORG = "radkit-to-grafana"
INFLUXDB_BUCKET = "my-radkit-bucket"
CONFIG_YAML = "/app/radkit-to-grafana-config/config.yaml"
SECRET_FILE_PATH = "/run/secrets/radkit_credentials.b64"
SECRET_ENV_NAME = "RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64"

# Global variables for client and service
client = None
service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    Manage RADKit client lifecycle - startup and shutdown.
    
    This lifespan context manager is required because:
    
    1. RADKit's Client.create() returns a context manager that must be properly
       entered and exited to manage the connection lifecycle.
    
    2. When using uvicorn with reload=True and the "main:app" import string format,
       the application module is re-imported on each reload. Without this lifespan
       manager, the RADKit client would not be initialized.
    
    3. FastAPI's lifespan feature ensures that:
       - The RADKit client is initialized ONCE on application startup
       - The client connection persists across all API requests
       - The client is properly cleaned up when the application shuts down
       - On hot-reload, the old connection is closed and a new one is created
    
    How it works:
    - Code before 'yield' runs on application startup
    - The 'yield' statement keeps the context active while the app runs
    - Code after 'yield' runs on application shutdown
    - The client and service are stored as global variables accessible to all endpoints
    
    This pattern enables hot-reload functionality while maintaining proper
    resource management for the RADKit client connection.
    '''
    global client, service
    
    if not os.path.exists(SECRET_FILE_PATH):
        print(f"⚠️ Error: Secret file '{SECRET_FILE_PATH}' not found.", flush=True)
        print("⚠️ Please ensure it is mounted when running the container", flush=True)
        sys.exit(1)
    
    try:
        with open(SECRET_FILE_PATH, 'r') as f:
            encoded_password = f.read().strip()

        os.environ[SECRET_ENV_NAME] = encoded_password
        
        with open(CONFIG_YAML, 'r') as f:
            config_data = yaml.safe_load(f)
            
        radkit_grafana = config_data.get('radkit-config', {})
        radkit_service_username = radkit_grafana.get('radkit-service-username')
        radkit_service_code = radkit_grafana.get('radkit-service-code')

        # Enter the context manager for the client
        client_cm = Client.create()
        client = client_cm.__enter__()
        client_auth = client.certificate_login(radkit_service_username)
        service = client_auth.service(radkit_service_code).wait()
        
        print("✅ RADKit service initialized successfully", flush=True)
        
        yield  # Application runs here
        
        # Cleanup on shutdown
        print("🔄 Shutting down RADKit service...", flush=True)
        client_cm.__exit__(None, None, None)
        
    except Exception as e:
        print(f"❌ Error initializing RADKit service: {e}", flush=True)
        sys.exit(1)

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def read_root():
    '''
    Tests the connection to this server. For docker compose health-checks.
    '''
    return {"status": "ok"}


@app.get("/devices")
def get_devices():
    '''
    Retrieves a list of all devices available in the RADKit service inventory.
    '''
    return { device.name for device in service.inventory.values() }


@app.get("/device/{device_name}/exec/{cmd}")
def exec_show_cmd(device_name: str, cmd:str) -> Any:
    '''
    Executes any given command on a specified device and returns the raw output.
     - device_name: The name of the device as defined in RADKit inventory.
     - cmd: The CLI command to execute (e.g., "show version").
     - Returns: The raw output of the command execution.
    '''
    single_result = service.inventory[device_name].exec(cmd).wait()
    return single_result.result.data


@app.get("/device/{device_name}/interfaces")
def get_interfaces(device_name: str) -> list[str]:
    '''
    Retrieves a list of all the interfaces of a device.
    - device_name: The name of the device as defined in RADKit inventory.
    - Returns: A list of interface names.
    '''
    try:
        raw_result = service.inventory[device_name].exec("show interfaces summary").wait()
        parsed_result = radkit_genie.parse(raw_result).to_dict()
        interfaces_list = parsed_result[device_name]["show interfaces summary"]["interfaces"]
        return list(interfaces_list.keys())
    except Exception as ex:
        print(f"⚠️ Issue with query (show interfaces summary) on device ({device_name}) - {ex}")
        return ["ERROR"]


@app.get("/device/{device_name}/interface-details")
def get_interface_details_device(device_name: str) -> list:
    """
    Retrieve detailed interface information from a network device.
    Returns data in a homogeneous format regardless of device type, ideal for Grafana visualization.
    
    CLI Commands:
    - Cisco IOS/IOS-XE: show ip interface brief
    - Cisco IOS-XR: show ipv4 interface brief
    """
    # Fetch device from RADKit inventory
    device = service.inventory[device_name]
    
    # Get device type from device metadata
    device_type = str(device.device_type).lower() if hasattr(device, 'device_type') else ''
    
    # Execute CLI command based on device type
    if device_type in ["cisco_ios", "cisco_xe", "ios", "iosxe", "ios_xe"]:
        result = device.exec("show ip interface brief").wait()
        command_key = "show ip interface brief"
    elif device_type in ["cisco_xr", "iosxr", "ios_xr"]:
        result = device.exec("show ipv4 interface brief").wait()
        command_key = "show ipv4 interface brief"
    else:
        raise ValueError(f"Unsupported device type: {device_type}")
    
    # Parse with radkit_genie
    parsed = radkit_genie.parse(result)
    values = parsed[device_name][command_key].data
    
    # Homogenize data across device types
    result_list = []
    
    if device_type in ["cisco_ios", "cisco_xe", "ios", "iosxe", "ios_xe"]:
        # Process Cisco IOS/IOS-XE format
        for interface_name, interface_data in values.get('interface', {}).items():
            homogenized_item = {
                'name': interface_name,
                'ip_address': interface_data.get('ip_address', 'unassigned'),
                'status': interface_data.get('status', 'unknown'),
                'protocol': interface_data.get('protocol', 'unknown')
            }
            result_list.append(homogenized_item)
    
    elif device_type in ["cisco_xr", "iosxr", "ios_xr"]:
        # Process Cisco IOS-XR format to match the same structure
        for interface_name, interface_data in values.get('interface', {}).items():
            homogenized_item = {
                'name': interface_name,
                'ip_address': interface_data.get('ipv4', {}).get('ip', 'unassigned') if isinstance(interface_data.get('ipv4'), dict) else 'unassigned',
                'status': interface_data.get('status', 'unknown'),
                'protocol': interface_data.get('protocol', 'unknown')
            }
            result_list.append(homogenized_item)
    
    # Return as list for Grafana
    return result_list


@app.get("/device/{device_name}/interfaces/traffic")
def get_interface_traffic(device_name: str) -> Any:

    influxdb_points = []

    # Execute command and parse with Genie
    raw_result = service.inventory[device_name].exec("show interfaces").wait()
    parsed_result = radkit_genie.parse(raw_result).to_dict()

    # Process each interface and prepare data for InfluxDB
    for interface in parsed_result[device_name]["show interfaces"]:
        if "rate" in parsed_result[device_name]["show interfaces"][interface]["counters"].keys():
            in_rate = parsed_result[device_name]["show interfaces"][interface]["counters"]["rate"]["in_rate"]
            out_rate = parsed_result[device_name]["show interfaces"][interface]["counters"]["rate"]["out_rate"]
            total_rate = in_rate + out_rate
        else:
            total_rate = 0
        
        # Create an InfluxDB Point for each interface
        influxdb_points.append(
            Point("interface_traffic") \
                .tag("device", device_name) \
                .tag("interface", str(interface)) \
                .field("total_rate", total_rate)
            )
    
    # Write data to InfluxDB
    try:
        with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=influxdb_points)
            return {"status": True, "msg": f"{len(influxdb_points)} traffic points successfully written to InfluxDB."}

    except Exception as e:
        print(f"Error writing to InfluxDB: {e}")
        return {"status": True, "msg": f"Error: {e}"}


def main():
    '''
    Starts the FastAPI server.
    The server host and port are configured via `config.yaml`.
    '''
    try:
        with open(CONFIG_YAML, 'r') as f:
            config_data = yaml.safe_load(f)
            
        radkit_grafana = config_data.get('radkit-config', {})
        server_host = radkit_grafana.get('server-host')
        server_port = radkit_grafana.get('server-port')

        uvicorn.run(
            "main:app",
            host = server_host,
            port = server_port,
            reload = True
        )
            
    except Exception as e:
        print(f"Error: {e}", flush=True)
        sys.exit(1)
        
if __name__ == "__main__":
    main()