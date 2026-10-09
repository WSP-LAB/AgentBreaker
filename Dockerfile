FROM python:3.10-slim

WORKDIR /app

COPY framework ./framework
COPY llm ./llm
COPY requirements.txt .
COPY generate_agents_compose_file.py .
COPY test_deploy_execute.py .
COPY attack.py .
COPY main.py .

RUN pip install -r requirements.txt