# This Makefile contains the following targets:
#
# - build: 	Builds the Docker image for the FastAPI middleware application.
# 			It uses the Dockerfile located in the 'radkit-to-grafana-fastapi-middleware/' directory
# 			and tags the image as 'fastapi-middleware'.
#
# - run: 	Sets up and starts the radkit-to-grafana services using Docker Compose.
# 			It first prompts the user for a password, base64 encodes it, and saves it
# 			to a temporary secret file ('radkit-to-grafana-agent-config/.radkit_user.b64').
# 			Then, it starts the Docker Compose services in detached mode, waiting for them
# 			to become healthy (up to 120 seconds).
#
# - clean: 	Stops and removes all Docker Compose services, removes the
# 			'fastapi-middleware' Docker image, and deletes the temporary secret file.
#
# - onboard: 	Builds and runs a Docker container for client onboarding.
# 				It builds an image named 'radkit-client-onboarding' using a specific Dockerfile
# 				located in 'radkit-to-grafana-client-onboarding/'. Then, it runs this container
# 				interactively, mounting the 'radkit-to-grafana-agent-config' directory into it.

.PHONY: build run clean onboard

# Container image name
IMAGE_NAME := fastapi-middleware
# Application directory
APP_DIR := radkit-to-grafana-fastapi-middleware/
# Temporary secret file name (created in the current directory)
SECRET_FILE := radkit-to-grafana-agent-config/.radkit_user.b64

all: up

build:
	@echo "--- 🏗️ Building the fastapi-middleware image ---"
	docker build -t $(IMAGE_NAME) $(APP_DIR)
	@echo "---------------------------------------------"

run:
	@echo "--- 🚀 Setting up the radkit-to-grafana services ---"
	@read -s -p "🔑 Enter the Private Key password of 'radkit-service-username' from your config.yaml file: " USER_PASSWORD; \
	ENCODED_PASSWORD=$$(printf "%s" "$$USER_PASSWORD" | base64); \
	echo ""; \
	echo "$$ENCODED_PASSWORD" > $(SECRET_FILE); \
	chmod 600 $(SECRET_FILE); \
	docker compose up -d --wait --wait-timeout 120
	@echo "---------------------------------------------"
	@echo "--- ✅ radkit-to-grafana services up and running! ---"
	@echo "---------------------------------------------"


up: build run

stop:
	@echo "--- 🛑 Stopping all services ... ---"
	docker compose stop
	@echo "-----------------------------"
	@echo "--- 🛑 Stopping complete! ---"
	@echo "-----------------------------"

clean:
	@echo "--- 🧹 Cleaning up ... ---"
	docker compose down
	docker rmi $(IMAGE_NAME) || true
	rm -rf $(SECRET_FILE)
	@echo "--------------------------------"
	@echo "--- 🧹 Cleaning up complete! ---"
	@echo "--------------------------------"

onboard:
	docker build -f radkit-to-grafana-client-onboarding/Dockerfile -t radkit-client-onboarding .
	docker run -it --rm \
		-v "$(PWD)/radkit-to-grafana-agent-config:/radkit-to-grafana-agent-config" \
		radkit-client-onboarding