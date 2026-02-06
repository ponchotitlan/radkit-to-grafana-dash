# Demo

## URLs

| Description | URL |
|-------------|-----|
| Get the devices | http://localhost:8000/devices |
| Execute a random command | http://localhost:8000/device/ksp-g01-asr1001x-10/exec/show%20ip%20interface%20brief |
| Parse a random command | http://localhost:8000/device/ksp-g01-asr1001x-10/parse/show%20ip%20interface%20brief |
| Parse for Grafana | http://localhost:8000/device/ksp-g01-asr1001x-10/interface-details |
| Interface traffic record | http://localhost:8000/device/ksp-g01-asr1001x-10/interfaces/traffic<br>http://localhost:8000/device/p0-2e/interfaces/traffic |

## Agent prompt

Please create an API endpoint for interface brief. The expected output from the genie parser is the following: 
...
Keep the interface name, ip_address, status and protocol

## Hardware Dashboard

| Type | Value |
|------|-------|
| URL | /device/${Device}/version |

## Interfaces Dashboard

| Field | Value |
|-------|-------|
| URL | /device/${Device}/interfaces/brief |
| name | 🔌 Name |
| ip_address | 🔀 IP Address |
| protocol | 🌐 Protocol Status |
| status | 🔗 Interface Status |
| up | ✅ |
| down | 🔥 |


## Time-series Dashboard

| Type | Configuration |
|------|---------------|
| Query | `from(bucket: "my-radkit-bucket")`<br>`  \|> range(start: v.timeRangeStart, stop: v.timeRangeStop)`<br>`  \|> filter(fn: (r) => r["_measurement"] == "interface_traffic")`<br>`  \|> filter(fn: (r) => r["_field"] == "total_rate")`<br>`  \|> filter(fn: (r) => r["device"] == "${Device}")` |
| Transformation | Rename fields by regex |
| | Match `.*interface="([^"]+)".*` |
