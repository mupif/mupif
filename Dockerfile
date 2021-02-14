FROM ubuntu:20.04
LABEL maintainer="vaclav.smilauer@fsv.cvut.cz"
LABEL version="0.1"
LABEL description="Containerized MuPIF for testing"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
# python3-vtk7 pulls extra 160MB, but pip download is over 100MB as well
RUN apt-get -y install python3-vtk7 python3-numpy python3-scipy python3-nose python3-h5py python3-matplotlib python3-msgpack python3-pip
ENV MUPIF "/tmp/mupif"
ADD ./requirements.txt $MUPIF/
RUN cd $MUPIF; pip3 install -r requirements.txt
COPY . $MUPIF
RUN cd $MUPIF; python3 setup.py install

