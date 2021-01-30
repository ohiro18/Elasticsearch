angular.module('recsApp')
  .controller('LikedItemSearchCtrl', function(esClient) {
    ItemSearch = this;

    ItemSearch.searchString = "";
    ItemSearch.hits = [];
    ItemSearch.run = function() {
      // search ES by title, show results
      var esQuery = {
        "query": {
					"bool": {
            "should": [
              {"match": {
                "title": {
                  "query": ItemSearch.searchString
                }
              }},
              {
                "match_phrase_prefix": {
                  "title": ItemSearch.searchString
                }
              },
              {
                "match_phrase_prefix": {
                  "title_sentinel": {
                    "query":  "SENTINEL_BEGIN " + ItemSearch.searchString,
                    "boost": 100
                  }
                }
              }
            ]
				  }
        }
      };

      esClient.search({
        index: 'ml_tmdb',
        type: 'Item',
        body: esQuery
      }).then(function success(resp) {
        ItemSearch.hits = [];
        angular.forEach(resp.hits.hits, function(hit) {
          ItemSearch.hits.push(hit._source);
        });
      });
    };
});
