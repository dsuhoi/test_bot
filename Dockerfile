FROM python:3.10-slim

WORKDIR /test_bot

RUN apt-get update && apt-get install -y libcairo2

COPY start.py requirements.txt ./
COPY app/ ./app/

RUN pip install -r requirements.txt

# ENTRYPOINT ["python", "start.py"]
