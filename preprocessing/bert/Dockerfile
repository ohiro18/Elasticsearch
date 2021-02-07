FROM ubuntu:18.04
LABEL version="1.0"

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git

RUN pip3 install --upgrade pip

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN apt-get update && \
    apt-get install -y locales && \
    locale-gen ja_JP.UTF-8 && \
    echo "export LANG=ja_JP.UTF-8" >> ~/.bashrc

RUN echo "alias python=python3" >> $HOME/.bashrc && \
    echo "alias pip=pip3" >> $HOME/.bashrc

WORKDIR /work

CMD ["/bin/bash"]
