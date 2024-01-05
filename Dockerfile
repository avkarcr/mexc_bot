FROM python:3.10-slim
RUN mkdir /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt --no-cache-dir
COPY . /app
WORKDIR /app
RUN --mount=type=secret,id=ADMIN_ID cat /run/secrets/ADMIN_ID
CMD ["python", "main.py"]
