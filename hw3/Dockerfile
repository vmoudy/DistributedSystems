FROM ubuntu:latest
MAINTAINER Griffin Meyer “glmeyer@ucsc.edu”
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /kvs
WORKDIR /kvs
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["kvs.py"]