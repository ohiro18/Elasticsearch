angular.module('recsApp')
  .factory('recsSvc', recsSvc);

recsSvc.$inject = ['esClient', '$q', '$http', 'graphUtils'];

function recsSvc(esClient, $q, $http, graphUtils) {
  return {
    recommend: recommend
  };

  function fetchItemDetails(ItemIds) {
    var Items = [];
    var deferred = $q.defer();
    esClient.mget({
      index: 'ml_tmdb',
      type: 'Item',
      body: {ids: ItemIds}}).then(function(resp) {
        var Items = [];
        angular.forEach(resp.docs, function(doc) {
          var Item = doc._source;
          if (Item) {
            Items.push(Item);
          }
        });
        deferred.resolve(Items);
      });
    return deferred.promise;
  }

  function constructGuidingQuery(likes, config) {
    if (config.globalGuidance) {
      return {
        "match_all": {
        }
      };
    }
    var likedIds = [];
    angular.forEach(likes, function(likedItem) {
      likedIds.push(likedItem.mlensId);
    });
    ItemIdqStr = likedIds.join(' OR ');
    var minShouldMatch = config.minItems ? config.minItems : 0;
    queryClause1 = {"query_string": {
                      "query": ItemIdqStr,
                      "fields": ["liked_Items"],
                      "minimum_should_match": "" + (minShouldMatch) + "%"
                    }};
    return queryClause1;
  }

  function constructAdHocQuery(likes, config) {


    var genreCutoffPercentage = 35.0;
    var allGenres = {};
    var allYears = {};
    var overviewTexts = [];


    angular.forEach(likes, function(likedItem) {
      if (likedItem.hasOwnProperty('overview')) {
        overviewTexts.push(likedItem.overview);
      }
      angular.forEach(likedItem.genres, function(genre) {
        if (likedItem.hasOwnProperty('release_date')) {
          var releaseYear = likedItem.release_date.substr(0,4);
          releaseHalfDecade = (5 * ~~(parseInt(releaseYear) / 5)).toString(); // hack to force integer division
          if (!allYears.hasOwnProperty(releaseHalfDecade)) {
            allYears[releaseHalfDecade] = 0;
          }
          else {
            allYears[releaseHalfDecade] += 1;
          }
        }
        if (!allGenres.hasOwnProperty(genre.name)) {
          allGenres[genre.name] = 0;
        }
        allGenres[genre.name] += 1;
      });
    });

    // include popular genres
    var genreCutoff = 0;
    var likedGenres = [];
    angular.forEach(allGenres, function(cnt, genre) {
      if (cnt > genreCutoff) {
        likedGenres.push(genre.toLowerCase().replace('/ /g', '_'));
      }
    });

    // include popular years
    var cutoff = 0;
    var likedHalfDecades = [];
    angular.forEach(allYears, function(cnt, year) {
      if (cnt > cutoff) {
        likedHalfDecades.push(year);
      }
    });

    // include overview text
    likeGenreqStr = likedGenres.join(' OR ');
    likeYearQStr = likedHalfDecades.join(' OR ');


    queryClause2 = {"query_string": {
                      "query": likeGenreqStr,
                      "fields": ["liked_genres"],
                      "boost": 1.0
                    }};
    queryClause3 = {"query_string": {
                      "query": likeYearQStr,
                      "fields": ["liked_years"],
                      "boost": 1.0
                    }};

    queryClause4 = {"more_like_this": {
                      "fields": ["liked_overview"],
                      "like": overviewTexts,
                      "boost": 3.0
                   }};

    // some more features layered in
    query = {'bool': {'should': [constructGuidingQuery(likes, config)]}};
    if (config.useGenre) {
      query.bool.should.push(queryClause2);
    }
    if (config.useDate) {
      query.bool.should.push(queryClause3);
    }
    if (config.useOverviews) {
      query.bool.should.push(queryClause4);
    }
    return query;
  }

  function recommend(user, config) {
    var qConfig = angular.copy(config);
    qConfig.globalGuidance = false;
    query = constructAdHocQuery(user.likes, qConfig);

    likedIds = [];
    angular.forEach(user.likes, function(likedItem) {
      likedIds.push(likedItem.mlensId);
    });

    var esQuery=  {
          "query": query,
          "vertices": [
              {
                  "field": "liked_Items",
                  "exclude": likedIds
              }
          ],
         "controls": {
            "use_significance": true,
            "sample_size": config.numSimilarUsers // this many relevant results used in sig terms
          },
          "connections": {
              "query": constructGuidingQuery(user.likes, {minItems: 0, globalGuidance: config.globalGuidance}), // guide only in the context of these recs, not globally
              "vertices": [ // how many degrees of kevin bacon
                  {"field": "liked_Items",
                   "exclude": likedIds}
              ]
          }
    };
    $http.post(esBaseURL + '/Itemlens/_graph/explore', esQuery)
    .success(function(resp) {
      // Items of depth 0 are statistically significant in the top <sample_size>
      // search results of the query
      var allItems = resp.vertices;
      var usersItems = graphUtils.parse(resp.vertices, resp.connections);

      // sort by depth so 0 depth first, helps
      // organize the graph

      relatedItemIds = [];
      angular.forEach(allItems, function(ItemVertex) {
        var ItemId = ItemVertex.term;
        relatedItemIds.push(ItemId);
      });
      fetchItemDetails(relatedItemIds)
      .then(function success(ItemDetails) {

        // hash by ItemId
        ItemDetailsLookup = {};
        angular.forEach(ItemDetails, function(ItemDetail) {
          ItemDetailsLookup[ItemDetail.mlensId] = ItemDetail;
        });

        // connect Items to one-another via graph
        angular.forEach(usersItems, function(userItem) {
          var currItem = ItemDetailsLookup[userItem.term];
          if (currItem) {
            currItem.related = [];
            angular.forEach(userItem.outbound, function(connectedItem) {
              var connectedItemDetailed = ItemDetailsLookup[connectedItem.term];
              currItem.related.push(connectedItemDetailed);
            });
          }
        });

        // add details to Items are related to this user
        var thisUsersItems = [];
        angular.forEach(usersItems, function(ItemVertex) {
          thisUsersItems.push(ItemDetailsLookup[ItemVertex.term]);
        });

        // organize a graph based on these details
        user.relatedItems = thisUsersItems;
      }, function error(err) {
        console.log(err);
      }

      );

      // Items of depth 1 are significant to the Item at depth 0 it's connected to

      console.log(resp);
    });

  }
}
