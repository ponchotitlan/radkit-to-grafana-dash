import os
import sys
import yaml
import uvicorn
import radkit_genie
from fastapi import FastAPI
from radkit_client.sync import Client

INFLUXDB_URI = "http://influxdb:8086"
CONFIG_YAML = "/app/radkit-to-grafana-agent-config/config.yaml"
SECRET_FILE_PATH = "/run/secrets/radkit_credentials.b64"
SECRET_ENV_NAME = "RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64"

CMD_INTERFACE_NAMES = "show interfaces summary"

app = FastAPI()

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


@app.get("/device/{device_name}/interfaces")
def get_interfaces(device_name: str) -> list[str]:
    '''
    Retrieves a list of all the interfaces of a device.
    '''
    try:
        raw_result = service.inventory[device_name].exec(CMD_INTERFACE_NAMES).wait()
        parsed_result = radkit_genie.parse(raw_result).to_dict()
        interfaces_list = parsed_result[device_name][CMD_INTERFACE_NAMES]["interfaces"]
        return list(interfaces_list.keys())
    except Exception as ex:
        print(f"⚠️ Issue with query ({CMD_INTERFACE_NAMES}) on device ({device_name}) - {ex}")
        return ["ERROR"]
    

def main():
    '''
    Establishes a session with the local RADKit Service and starts the FastAPI server.
    The server host and port are configured via `config.yaml`.
    '''
    global client
    global service
        
    if os.path.exists(SECRET_FILE_PATH):
        try:
            with open(SECRET_FILE_PATH, 'r') as f:
                encoded_password = f.read().strip()

            os.environ[SECRET_ENV_NAME] = encoded_password
            with Client.create() as rk_client:
                with open(CONFIG_YAML, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                radkit_grafana = config_data.get('radkit-config', {})
                server_host = radkit_grafana.get('server-host')
                server_port = radkit_grafana.get('server-port')
                radkit_service_username = radkit_grafana.get('radkit-service-username')
                radkit_service_code = radkit_grafana.get('radkit-service-code')

                client = rk_client.certificate_login(radkit_service_username)
                service = client.service(radkit_service_code).wait()
                uvicorn.run(
                    app,
                    host = server_host,
                    port = server_port,
                    reload = False
                )
                
        except Exception as e:
            print(f"Error: {e}", flush=True)
            sys.exit(1)
    else:
        print(f"⚠️ Error: Secret file '{SECRET_FILE_PATH}' not found.", flush=True)
        print("⚠️ Please ensure it is mounted when running the container (e.g., -v /host/path:/container/path)", flush=True)
        sys.exit(1)
        
if __name__ == "__main__":
    main()