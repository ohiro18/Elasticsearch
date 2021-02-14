#!/bin/bash

sleep 15

echo "Running __init__.py"
python /etl/__init__.py

until wait-for-it.sh elasticsearch:9200  ";" ; do
	echo "Waiting on Elasticsearch init..."
	sleep 5
done

echo "Running index.py"
python /etl/index.py

echo "Running ratingsToEs.py"
python /etl/ratingsToEs.py http://elasticsearch:9200 /etl/ml_tmdb.json /etl/ml-20m/ratings.csv

echo "Done with setup"
