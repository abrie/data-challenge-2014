"use strict";

$( document ).ready( main );

function main() {
    $.getJSON("results.json", function(d) {
        displayData( processData(d) );
    }); 
}

function displayData( graph ) {
    var width = 960,
    height = 500;

    var color = d3.scale.category20();

    var radius = d3.scale.sqrt()
    .range([0, 6]);

    var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height);

    var force = d3.layout.force()
    .size([width, height])
    .charge(-400)
    .linkDistance(function(d) { 
        return radius(d.source.size)*5 + radius(d.target.size)*5 ; 
    });

  force
      .nodes(graph.nodes)
      .links(graph.links)
      .on("tick", tick)
      .start();
  var link = svg.selectAll(".link")
      .data(graph.links)
    .enter().append("path")
      .attr("class","link");

  var node = svg.selectAll(".node")
      .data(graph.nodes)
    .enter().append("g")
      .attr("class", "node")
      .call(force.drag);

  node.append("circle")
      .attr("r", function(d) { return radius(d.size); })
      .style("fill", function(d) { return color(d.atom); });

  function tick() {
    link.attr("d", function(d) {
      var x1 = d.source.x,
          y1 = d.source.y,
          x2 = d.target.x,
          y2 = d.target.y,
          dx = x2 - x1,
          dy = y2 - y1,
          dr = Math.sqrt(dx * dx + dy * dy),

          // Defaults for normal edge.
          drx = dr,
          dry = dr,
          xRotation = 0, // degrees
          largeArc = 0, // 1 or 0
          sweep = 1; // 1 or 0

          // Self edge.
          if ( x1 === x2 && y1 === y2 ) {
            // Fiddle with this angle to get loop oriented.
            xRotation = -45;

            // Needs to be 1.
            largeArc = 1;

            // Change sweep to change orientation of loop. 
            //sweep = 0;

            // Make drx and dry different to get an ellipse
            // instead of a circle.
            drx = 30;
            dry = 20;
            
            // For whatever reason the arc collapses to a point if the beginning
            // and ending points of the arc are the same, so kludge it.
            x2 = x2 + 1;
            y2 = y2 + 1;
          } 

     return "M" + x1 + "," + y1 + "A" + drx + "," + dry + " " + xRotation + "," + largeArc + "," + sweep + " " + x2 + "," + y2;
    });

    node.attr("transform", function(d) {
        return "translate(" + d.x + "," + d.y + ")"; 
    });
  }
}

function processData( theData ) {
    var nodeList = [];
    var linkList = [];

    function findNodes( dict ) {
        for( var key in dict ) {
            var index = nodeList.indexOf( key );
            if( index < 0 ) {
                nodeList.push( key );
            }
        }
    }

    // Build an array of nodes
    findNodes( theData );

    function findLinks( dict ) {
        for( var key in dict ) {
            var connectedDict = dict[key];
            var sourceIndex = nodeList.indexOf( key );
            for( var connectedKey in connectedDict ) {
                if( connectedDict[connectedKey] > 0.10 ) {
                    var targetIndex = nodeList.indexOf( connectedKey );
                    var value = 1;
                    var link = {
                        source: sourceIndex,
                        target: targetIndex,
                        value: value
                    }
                    linkList.push( link );
                }
            }
        }
    }

    findLinks( theData );

    nodeList = nodeList.map( function(item, index) {
        return {
            name: item,
            group: index,
            size: 6,
        }
    });

    var result = {
        nodes: nodeList,
        links: linkList,
    }

    return result;
}
