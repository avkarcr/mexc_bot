FROM python:3.10-slim
RUN mkdir /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt --no-cache-dir
COPY . /app
WORKDIR /app
ENV ADMIN_ID=${{ secrets.ADMIN_ID }
ENV TELEGRAM_TOKEN=${{ secrets.TELEGRAM_TOKEN }}
ENV MEXC_API=${{ secrets.MEXC_API }}
ENV MEXC_SECRET_KEY=${{ secrets.MEXC_SECRET_KEY }}
CMD ["python", "main.py"]
