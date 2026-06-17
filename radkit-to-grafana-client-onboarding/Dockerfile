# Base image: Specifies the base image to use for building the Docker image.
FROM python:3.10-slim

# Working directory: Sets the working directory inside the container to /app.
WORKDIR /app

# Install RADKit dependencies using RADKit index in addition to PyPI.
RUN pip install --no-cache-dir --extra-index-url https://radkit.cisco.com/pip cisco-radkit-client==1.9.6 pyaml

# Copy application files: Copies all files from the specified subdirectory (radkit-to-grafana-client-onboarding) on the host to the /app directory in the container.
COPY radkit-to-grafana-client-onboarding/. /app

# Command to run the application: Specifies the command to execute when the container starts.
CMD ["python", "main.py"]