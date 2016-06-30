Zoodocker
---------

Automatic management of container configuration with Zookeeper.

Build
-----

    $ docker build -t 'kamikat/zoodocker' .

Usage
-----

Starting a daemon:

    $ docker run \
        --restart=always \
        -v /var/run/docker.sock:/var/run/docker.sock
        -v $HOME/.docker:/root/.docker \
        -e ZK_HOST=<ip:port> \
        -e SERVICE_ID=<service_id> \
        --name zoodocker \
        kamikat/zoodocker:latest

Zoodocker daemon should start with docker daemon automatilly, listening changes for `<service_id>` from Zookeeper.

Place a `docker-compose.yml` in root of your service configuration
and Zoodocker daemon should pick that to start your container.

Upload a configuration of `<service_id>`:

    $ ./upload.py <service_id> <config_dir>

Test environment:

1. Get [docker-compose](https://docs.docker.com/compose/install/)
2. Start docker management daemon

    `ZK_HOST=172.17.42.1:2181 SERVICE_ID=test docker-compose up`

Example
-------

    $ docker run \
        --restart=always \
        -v /var/run/docker.sock:/var/run/docker.sock
        -v $HOME/.docker:/root/.docker \
        -e ZK_HOST=172.17.42.1:2181 \
        -e SERVICE_ID=test \
        --name zoodocker_test \
        kamikat/zoodocker:latest

Upload configuration in `test/1` to `zk:///service/test`
(the prefix `/service` can be overriden with environment variable `SERVICE_NAMESPACE`).

    $ ./upload.py test test/1

And Zoodocker daemon should start a container running python simple http server.

License
-------

(The MIT License)

