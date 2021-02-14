angular.module('recsApp')
  .controller('CustomRecsCtrl', function(esClient, recsSvc, $scope, $log) {
    // Allow searches on title
    var customRecs = this;

    var storedLikes = localStorage.ItemLibrary ? JSON.parse(localStorage.ItemLibrary) : null;
    customRecs.recs = {likes:
                       storedLikes || [],
                       config: {
                         useDate: false,
                         useGenre: false,
                         useOverviews: false,
                         numSimilarUsers: 1000,
                         minItems: 50, 
                         globalGuidance: false

                       }};
    customRecs.mode = 'define';

    customRecs.addItem = function (Item) {
      customRecs.recs.likes.push(Item);
      localStorage.ItemLibrary = JSON.stringify(customRecs.recs.likes);
    };

    customRecs.removeItem = function (Item) {
      var ItemIndex = customRecs.recs.likes.indexOf(Item);
      if (ItemIndex >= 0) {
        customRecs.recs.likes.splice(ItemIndex, 1);
        localStorage.ItemLibrary = JSON.stringify(customRecs.recs.likes);
      }
    };

    customRecs.recs.setMode = function(mode) {
      if (mode === "relevance") {
        customRecs.recs.config.useOverviews = true;
      }
      customRecs.mode = mode;
      customRecs.recs.run();
    };

/*    customRecs.recs.run = function() {
      recsSvc.recommend(customRecs.recs, customRecs.recs.config);
    };
*/

  });
