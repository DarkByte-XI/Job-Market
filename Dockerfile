FROM ubuntu:latest
LABEL authors="dani"

ENTRYPOINT ["top", "-b"]