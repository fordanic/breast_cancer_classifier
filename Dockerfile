FROM pytorch/pytorch:latest
RUN apt-get update 
RUN apt-get install -y \
    gcc \
    git \
    libgtk2.0-dev \
    apt-utils
RUN mkdir input
RUN mkdir output
COPY . /app
RUN pip install -r /app/requirements.txt
