FROM python:3-bullseye

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN apt install libmagickwand-dev
RUN pip install -r requirements.txt

COPY ./ink-server /app

VOLUME /app/data
EXPOSE 8080

ENTRYPOINT [ "python3", "/app/main.py" ]