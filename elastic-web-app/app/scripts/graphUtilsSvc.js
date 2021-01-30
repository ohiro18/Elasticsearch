angular.module('recsApp')
  .factory('graphUtils', graphUtils);

function graphUtils() {
  return {
    parse: parse
  };

  function parse(vertices, connections) {

    function getOutbound(listIdx) {
      var outbounds = [];
      angular.forEach(connections, function(connection) {
        if (connection.source === listIdx) {
          outbounds.push(connection);
        }
      });
      return outbounds;
    }

    function getConnectionsAtDepth(listIdx, depth) {
      var outbound = getOutbound(i);
      var outboundAtDepth = [];
      angular.forEach(outbound, function(connection) {
        var targetVtx = vertices[connection.target];
        if (targetVtx.depth === depth) {
          outboundAtDepth.push(targetVtx);
        }
      });
      return outboundAtDepth;
    }

    var i = 0;
    var rootVertices = [];
    for (i = 0; i < vertices.length; i++) {
      var vertex = vertices[i];
      if (vertex.depth === 0) {
        var nextOutbound = getConnectionsAtDepth(i, 1);
        vertex.outbound = nextOutbound;
        rootVertices.push(vertex);
      }
    }

    return rootVertices;
  }

}
