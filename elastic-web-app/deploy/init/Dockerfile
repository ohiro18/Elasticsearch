FROM elasticsearch:2.4.4

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
#RUN rm -rf /etl/ml-20m
#RUN ./prepareData.sh

WORKDIR /
RUN python /etl/rehashTmdbToMl.py /etl/tmdb.json /etl/ml_tmdb.json

CMD /code/init.sh
