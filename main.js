"use strict";

$( document ).ready( main );

function generateSvgElement(id, width, height) {
    // as per http://stackoverflow.com/a/8215105
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute('style', 'border: 1px solid black');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('id', id);
    svg.setAttributeNS(
        "http://www.w3.org/2000/xmlns/",
        "xmlns:xlink",
        "http://www.w3.org/1999/xlink");

    return $(svg);
}

function main() {
    $.getJSON("data/results.json", function(d) {
        $("#graph").append( generateSvgElement("svg-group-0", 400, 400) );
        createClusterGraph( processData(d, 0), "#svg-group-0" );
        //displayData( processData(d), "#main-svg" );
    }); 
}

function displayData( graphData, element_id ) {
    // Create a new directed graph
    var g = new dagreD3.Digraph();

    graphData.nodes.forEach( function(node) {
        g.addNode(node.name, { 
            label: node.name,
            labelStyle: "font-size: 60em;" 
        });
    });

    graphData.links.forEach( function(edge) {
        var a = graphData.nodes[edge.source].name;
        var b = graphData.nodes[edge.target].name;
        var p = edge.probability;
        var appearance = { style: 'stroke-width: 20px;' };
        g.addEdge( null, a,b, appearance )
    });

    var renderer = new dagreD3.Renderer();
    renderer.run(g, d3.select(element_id));
    console.log("done.");
}

function createClusterGraph( graph, element_id ) {
    function name(d) { return d.name; }
    function group(d) { return d.group; }

    var color = d3.scale.category10();
    function colorByGroup(d) { return color(group(d)); }

    var svg = d3.select(element_id);
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

function processData( theData, cluster_id ) {
    var nodeList = [];
    var linkList = [];

    function findNodes( chains, clusters ) {
        for( var key in chains ) {
            var index = nodeList.indexOf( key );
            if( index < 0 ) {
                if( clusters[key] === cluster_id ) {
                    nodeList.push( key );
                }
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
            if( clusters[key] === cluster_id ) {
                for( var connectedKey in connectedDict ) {
                    if( clusters[connectedKey] === cluster_id ) { 
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
        clusters: clusters,
    }

    return result;
}

