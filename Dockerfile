FROM python:2.7

# Setup docker & docker-compose
RUN apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D && echo "deb http://apt.dockerproject.org/repo debian-jessie main" > /etc/apt/sources.list.d/docker.list && apt-get update && apt-get install -y docker-engine=1.8.1-0~jessie
RUN curl -L https://github.com/docker/compose/releases/download/1.5.2/docker-compose-`uname -s`-`uname -m` > /usr/bin/docker-compose && chmod +x /usr/bin/docker-compose

RUN pip install kazoo

WORKDIR /app

COPY daemon.py /usr/local/bin/daemon

CMD [ "python", "/usr/local/bin/daemon" ]

