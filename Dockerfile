FROM debian:bookworm-20240612
LABEL maintainer="vaclav.smilauer@fsv.cvut.cz"
LABEL version="0.1"
LABEL description="Containerized MuPIF for testing"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get -y install python3-pip wireguard wireguard-tools iproute2 iputils-ping
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
ENV MUPIF "/tmp/mupif"
COPY ./requirements.txt $MUPIF/
RUN rm /usr/lib/python3.11/EXTERNALLY-MANAGED
RUN pip3 install --only-binary=:all: --upgrade -r $MUPIF/requirements.txt
COPY . $MUPIF/
RUN cd $MUPIF; python3 setup.py install
# this adds wireguard (only used in docker-compose-wireguard.yml)
COPY ./tools/vpn/wireguard/*.conf /etc/wireguard/
