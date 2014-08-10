"use strict";

$( document ).ready( main );

function main() {
    $.getJSON("data/results.json", function(d) {
        displayData( processData(d) );
    }); 
}

function displayData( graph ) {
    function name(d) { return d.name; }
    function group(d) { return d.group; }

    var color = d3.scale.category10();
    function colorByGroup(d) { return color(group(d)); }

    var svg = d3.select("svg");
    var width = svg.attr("width");
    var height = svg.attr("height");

    var node, link;

    var voronoi = d3.geom.voronoi()
    .x(function(d) { return d.x; })
    .y(function(d) { return d.y; })
    .clipExtent([[-10, -10], [width+10, height+10]]);

    function recenterVoronoi(nodes) {
        var shapes = [];
        voronoi(nodes).forEach(function(d) {
            if (!d.length) {
                return;
            }

            var n = [];
            d.forEach(function(c) {
                n.push([ c[0] - d.point.x, c[1] - d.point.y ]);
            });
            n.point = d.point;
            shapes.push(n);
        });
        return shapes;
    }

    var force = d3.layout.force()
    .charge(-2000)
    .friction(0.3)
    .linkDistance( function(d) { 
        if( d.source.group == d.target.group ) {
            return 10;
        }
        else {
            return 300;
        }
    })
    .size([width, height]);

    force.on('tick', function() {
        node.attr('transform', function(d) { return 'translate('+d.x+','+d.y+')'; })
        .attr('clip-path', function(d) { return 'url(#clip-'+d.index+')'; });

        link.attr('x1', function(d) { return d.source.x; })
        .attr('y1', function(d) { return d.source.y; })
        .attr('x2', function(d) { return d.target.x; })
        .attr('y2', function(d) { return d.target.y; });

        var clip = svg.selectAll('.clip')
        .data( recenterVoronoi(node.data()), function(d) { return d.point.index; } );

        clip.enter().append('clipPath')
        .attr('id', function(d) { return 'clip-'+d.point.index; })
        .attr('class', 'clip');
        clip.exit().remove();

        clip.selectAll('path').remove();
        clip.append('path')
        .attr('d', function(d) { return 'M'+d.join(',')+'Z'; });
    });

    graph.nodes.forEach(function(d, i) {
        d.id = i;
    });

    link = svg.selectAll('.link')
    .data( graph.links )
    .enter().append('line')
    .attr('class', 'link')
    .style("stroke-width", function(d) { return Math.sqrt(d.value); });

    node = svg.selectAll('.node')
    .data( graph.nodes )
    .enter().append('g')
    .attr('title', name)
    .attr('class', 'node')
    .call( force.drag );

    node.append('circle')
    .attr('r', 30)
    .attr('fill', colorByGroup)
    .attr('fill-opacity', 0.5);

    node.append('circle')
    .attr('r', 4)
    .attr('stroke', 'black');

    force
    .nodes( graph.nodes )
    .links( graph.links )
    .start();
}

function processData( theData ) {
    var nodeList = [];
    var linkList = [];

    function findNodes( chains, clusters ) {
        for( var key in chains ) {
            var index = nodeList.indexOf( key );
            if( index < 0 ) {
                nodeList.push( key );
            }
        }
    }

    // Build an array of nodes
    var chains = theData.chains
    var clusters = theData.clusters
    findNodes( chains, clusters );

    function findLinks( chains, clusters ) {
        for( var key in chains ) {
            var connectedDict = chains[key];
            for( var connectedKey in connectedDict ) {
                if( clusters[key] === clusters[connectedKey] ) { // in same group
                    var sourceIndex = nodeList.indexOf( key );
                    var targetIndex = nodeList.indexOf( connectedKey );
                    var probability = connectedDict[connectedKey].toFixed(2);
                    var value = 1;
                    var link = {
                        source: sourceIndex,
                        target: targetIndex,
                        probability: probability, 
                    }
                    linkList.push( link );
                }
            }
        }
    }

    findLinks( chains, clusters );

    nodeList = nodeList.map( function(item, index) {
        return {
            name: item,
            group: clusters[item],
            size: 6,
        }
    });

    var result = {
        nodes: nodeList,
        links: linkList,
    }

    return result;
}

