#!/bin/bash

sleep 15

# echo "Running indexMlTmdb.py"
# python /etl/indexMlTmdb.py http://elasticsearch:9200 /etl/ml_tmdb.json

echo "Running ratingsToEs.py"
python /etl/ratingsToEs.py http://elasticsearch:9200 /etl/ml_tmdb.json /etl/ml-20m/ratings.csv

echo "Done with setup"

