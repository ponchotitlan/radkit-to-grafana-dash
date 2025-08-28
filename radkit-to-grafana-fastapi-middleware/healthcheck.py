import urllib.request
import sys
import os

# Get the host and port from environment variables, or use defaults
# This makes the script more flexible
HEALTHCHECK_HOST = os.getenv("HEALTHCHECK_HOST", "127.0.0.1")
HEALTHCHECK_PORT = os.getenv("HEALTHCHECK_PORT", "8000")
HEALTHCHECK_PATH = os.getenv("HEALTHCHECK_PATH", "/health")
HEALTHCHECK_TIMEOUT = int(os.getenv("HEALTHCHECK_TIMEOUT", "5"))

url = f"http://{HEALTHCHECK_HOST}:{HEALTHCHECK_PORT}{HEALTHCHECK_PATH}"

print(f"Attempting health check for: {url} with timeout {HEALTHCHECK_TIMEOUT}s")

try:
    response = urllib.request.urlopen(url, timeout=HEALTHCHECK_TIMEOUT)
    if response.getcode() == 200:
        print("Healthcheck successful! Status code 200.")
        sys.exit(0)  # Exit with 0 for success
    else:
        print(f"Healthcheck failed: Received status code {response.getcode()}")
        sys.exit(1)  # Exit with 1 for failure
except urllib.error.URLError as e:
    print(f"Healthcheck failed: Network error or connection refused - {e}")
    sys.exit(1)
except Exception as e:
    print(f"Healthcheck failed: An unexpected error occurred - {e}")
    sys.exit(1)