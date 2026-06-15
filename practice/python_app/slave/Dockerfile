FROM python:3.9-slim
WORKDIR /
COPY requirements-slave.txt .
RUN pip install -r requirements-slave.txt
RUN mkdir -p /app/slave
COPY . /app/slave
CMD ["python", "/app/slave/slave.py"]
