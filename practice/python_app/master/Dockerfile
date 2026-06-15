FROM python:3.9-slim
WORKDIR /
COPY requirements-master.txt .
RUN pip install -r requirements-master.txt
RUN mkdir -p /app/master
COPY . /app/master
CMD ["python", "/app/master/master.py"]
