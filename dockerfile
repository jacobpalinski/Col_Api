FROM python:3.9-slim-buster

RUN apt-get update && apt-get install -y gcc musl-dev postgresql-server-dev-all

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["flask", "run", "--host=0.0.0.0", "--port=8088"]