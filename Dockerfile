FROM python:3.10-slim
RUN mkdir /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt
COPY main.py /app
WORKDIR /app
ENV TELEGRAM_TOKEN 1 
ENV ADMIN_ID 2
CMD ["python", "main.py"]
