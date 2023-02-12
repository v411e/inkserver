FROM python:3-bullseye

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN apt -y install libmagickwand-dev
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ./ink-server /app

VOLUME /app/data
EXPOSE 8080

ENTRYPOINT [ "python3", "/app/main.py" ]