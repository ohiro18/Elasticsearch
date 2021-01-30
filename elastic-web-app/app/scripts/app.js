angular.module('recsApp', ['elasticsearch']);

var esBaseURL = 'DYN_ELASTICSEARCH_URL';
angular.module('recsApp')
.service('esClient', function (esFactory) {
  return esFactory({
    host: esBaseURL
  });
});
