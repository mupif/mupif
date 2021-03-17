FROM ubuntu:20.04
LABEL maintainer="vaclav.smilauer@fsv.cvut.cz"
LABEL version="0.1"
LABEL description="Containerized MuPIF for testing"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get -y install python3-numpy python3-scipy python3-nose python3-h5py python3-matplotlib  python3-pip wireguard wireguard-tools iproute2 iputils-ping
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
ENV MUPIF "/tmp/mupif"
COPY ./requirements.txt $MUPIF/
RUN pip3 install -r $MUPIF/requirements.txt
COPY . $MUPIF/
RUN cd $MUPIF; python3 setup.py install
# this adds wireguard (only used in docker-compose-wireguard.yml)
COPY ./tools/vpn/wireguard/*.conf /etc/wireguard/
