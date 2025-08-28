# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy your Python script into the container
COPY collector.py .

# Install the requests library
RUN pip install --no-cache-dir requests

# Set the default command to run your script
CMD ["python3", "collector.py"]