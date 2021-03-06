import requests
import json
import os
import time
from requests.exceptions import ConnectionError
import urllib3

tmdb_api_key = os.environ["TMDB_API_KEY"]
tmdb_api = requests.Session()
tmdb_api.params={'api_key': tmdb_api_key}

urllib3.disable_warnings()

def movieList(linksFile='ml-20m/links.csv'):
    import csv
    rdr = csv.reader(open(linksFile))
    tmdbIds = {}
    numMissing = 0
    for rowNo, row in enumerate(rdr):
        if rowNo == 0:
            continue
        try:
            tmdbIds[row[0]] = int(row[2])
        except ValueError:
            numMissing += 1
            print("No TMDB ID at %s, imdb is: %s, missing %s/%s" % (row[0], row[1], numMissing, rowNo))
    return tmdbIds

def getCastAndCrew(movieId, movie):
    httpResp = tmdb_api.get("https://api.themoviedb.org/3/movie/%s/credits" % movieId, verify=False)
    credits = json.loads(httpResp.text) #C
    try:
        crew = credits['crew']
        directors = []
        for crewMember in crew: #D
            if crewMember['job'] == 'Director':
                directors.append(crewMember)
        movie['cast'] = credits['cast'] #E
        movie['directors'] = directors
    except KeyError as e:
        print e
        print credits

def extract(movieIds=[]):
    movieDict = {}
    for idx, (mlensId, tmdbId) in enumerate(movieIds.iteritems()):
        try:
            print("On %s / %s movies" % (idx, len(movieIds)))
            httpResp = tmdb_api.get("https://api.themoviedb.org/3/movie/%s"
                                    % tmdbId, verify=False)
            if int(httpResp.headers['x-ratelimit-remaining']) < 10:
                print("Rate limited, sleeping")
                time.sleep(6)
            movie = json.loads(httpResp.text)
            movie['mlensId'] = mlensId
            getCastAndCrew(tmdbId, movie)
            movieDict[tmdbId] = movie
        except ConnectionError as e:
            print e
        except ValueError:
            print('Bad JSON found.')
    return movieDict



if __name__ == "__main__":
    movieIds = movieList()
    movieDict = extract(movieIds)
    f = open('tmdb.json', 'w')
    f.write(json.dumps(movieDict))
