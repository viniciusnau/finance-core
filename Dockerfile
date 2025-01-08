FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8888
CMD gunicorn FINANCE_CORE.wsgi:application --bind 0.0.0.0:$PORT
