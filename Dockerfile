FROM debian:latest

RUN apt-get update
RUN apt-get install -y python3 python3-dev python3-pip python3-venv apache2 apache2-dev libapache2-mod-wsgi-py3
RUN apt-get install -y wget ca-certificates make gcc musl-dev

COPY apache2.conf /etc/apache2/
WORKDIR /data/local/app
COPY . /data/local/app

RUN python3 -m venv /data/local/venv
# Enable venv
ENV PATH="/data/local/venv/bin:$PATH"
RUN pip install -U pip setuptools wheel 
RUN pip install --no-cache-dir mod_wsgi
RUN pip install -r requirements.txt

RUN mkdir /flask_session
RUN chown www-data /flask_session
RUN chgrp www-data /flask_session

EXPOSE 80

CMD [ "apachectl", "-D", "FOREGROUND" ]
