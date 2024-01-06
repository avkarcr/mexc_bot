FROM python:3.10-slim
RUN mkdir /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt --no-cache-dir
COPY . /app
WORKDIR /app
ARG ADMIN_ID
ARG TELEGRAM_TOKEN
CMD ["python", "main.py"]
