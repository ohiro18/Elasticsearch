FROM elasticsearch:2.7.1

RUN apt-get update
RUN apt-get install python -y
RUN apt-get install python-pip -y
RUN pip install elasticsearch

COPY etl /etl
COPY deploy/init /code

RUN chown -R elasticsearch:elasticsearch /code
RUN chown -R elasticsearch:elasticsearch /etl

RUN ls /etl
WORKDIR /etl
RUN rm -rf /etl/ml-20m
RUN ./prepareData.sh

WORKDIR /
RUN python /etl/__init__.py

CMD /code/init.sh
