FROM python:3.10-slim
RUN mkdir /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt --no-cache-dir
COPY . /app
WORKDIR /app
ARG TELEGRAM_TOKEN
ARG ADMIN_ID
CMD ["python", "main.py"]
