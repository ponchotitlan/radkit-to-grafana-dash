# Base image: Specifies the base image to use for building the Docker image.
FROM python:3.9-slim

# Working directory: Sets the working directory inside the container to /app.
WORKDIR /app

# Copy requirements file: Copies the requirements.txt file from the host to the /app directory in the container.
COPY requirements.txt /app

# Install dependencies: Installs the Python dependencies listed in requirements.txt.
RUN pip install -r requirements.txt

# Copy application files: Copies all files from the current directory on the host to the /app directory in the container.
COPY . /app

# Command to run the application: Specifies the command to execute when the container starts.
CMD ["python", "main.py"]