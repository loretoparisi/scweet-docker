#
# Scweet Dockerfile
# @author Loreto Parisi (loretoparisi at gmail dot com)
# Copyright (c) 2020 Loreto Parisi
#

FROM python:3.7.4-slim-buster

LABEL maintainer Loreto Parisi loretoparisi@gmail.com

WORKDIR app

# google chrome
RUN apt-get -y update && \
    apt-get -y install wget
RUN cd /tmp && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb

# app requirements
COPY src/requirements.txt requirements.txt
RUN pip install -r requirements.txt

CMD ["bash"]