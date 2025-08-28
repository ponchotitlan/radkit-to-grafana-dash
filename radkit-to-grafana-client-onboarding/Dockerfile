FROM python:3.9-slim
WORKDIR /app
COPY radkit-to-grafana-client-onboarding/requirements.txt /app
RUN pip install -r requirements.txt
COPY radkit-to-grafana-client-onboarding/. /app
CMD ["python", "main.py"]