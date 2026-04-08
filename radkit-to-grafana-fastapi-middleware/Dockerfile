# Base image: Specifies the base image to use for building the Docker image.
FROM python:3.12-slim

# Working directory: Sets the working directory inside the container to /app.
WORKDIR /app

# Copy requirements file: Copies the requirements.txt file from the host to the /app directory in the container.
COPY requirements.txt /app

# Install dependencies: Installs the Python dependencies listed in requirements.txt.
RUN pip install -r requirements.txt

# Install RADKit dependencies using RADKit index in addition to PyPI.
RUN pip install --no-cache-dir --extra-index-url https://radkit.cisco.com/pip \
    cisco-radkit-client==1.9.6 \
    cisco-radkit-common==1.9.6 \
    cisco-radkit-service==1.9.6 \
    cisco-radkit-genie==1.9.6

# Note: Application files are mounted as a volume in docker-compose.yml for hot-reload support
# COPY . /app (removed - code is mounted at runtime)

# Command to run the application: Specifies the command to execute when the container starts.
CMD ["python", "main.py"]