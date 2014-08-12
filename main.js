"use strict";

$( document ).ready( main );

function generateSvgElement(id, width, height) {
    // as per http://stackoverflow.com/a/8215105
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('id', id);
    svg.setAttribute('preserveAspectRatio',"xMidYMid slice");
    svg.setAttribute('viewbox','0 0 200 200');
    svg.setAttributeNS(
        "http://www.w3.org/2000/xmlns/",
        "xmlns:xlink",
        "http://www.w3.org/1999/xlink");

    return $(svg);
}

function main() {
    $.getJSON("data/results.json", function( raw_data ) {
        var svgElement = generateSvgElement("main-svg", 300, 300);
        $("#graph").append( svgElement );
        displayData( raw_data , "#main-svg" );
    }); 
}

function displayData( raw_data, element_id ) {
    var graphData = linkData( condenseData(raw_data) );
    var g = new dagreD3.Digraph();

    graphData.nodes.forEach( function(node) {
        var id = "svg-sub-" + node.name;
        g.addNode(node.name, { 
            label: $("<div>").append( generateSvgElement(id, 200, 200) ).html(),
        });
    });

    graphData.links.forEach( function(edge) {
        var source = graphData.nodes[edge.source].name;
        var target = graphData.nodes[edge.target].name;
        var probability = edge.probability;
        var appearance = { style: 'stroke-width: 2px;' };
        g.addEdge( null, source, target, appearance )
    });

    var renderer = new dagreD3.Renderer();
    renderer.edgeInterpolate('cardinal');
    var layout = dagreD3.layout()
        .nodeSep(10)
        .edgeSep(25)
        .rankSep(30)
        .rankDir("TB");
    
    var element = d3.select( element_id );
    var rendered_layout = renderer.layout(layout).run(g, element);

    var colorSelector = d3.scale.category20();
    graphData.nodes.forEach( function(node) {
        var graph_id = "#svg-sub-" + node.name;
        createClusterGraph( linkData(raw_data, node.name), graph_id, colorSelector );
    });

    element.attr("width", rendered_layout.graph().width + 40);
    element.attr("height", rendered_layout.graph().height + 40);

    var zoom = d3.select("g.zoom", element);
    zoom.attr("transform","scale(0.25)");
}

function createClusterGraph( graph, element_id, colorSelector ) {
    function name(d) { return d.name; }

    function colorByGroup(d) { 
        return colorSelector( d.name ) ; 
    }

    var svg = d3.select(element_id);
    var width = svg.attr("width");
    var height = svg.attr("height");

    var node, link;

    var voronoi = d3.geom.voronoi()
        .x(function(d) { return d.x; })
        .y(function(d) { return d.y; });

    function recenterVoronoi(nodes) {
        var shapes = [];

        voronoi(nodes).forEach(function(d) {
            if(d.length) {
                var n = [];
                d.forEach(function(c) {
                    var x = c[0] - d.point.x;
                    var y = c[1] - d.point.y;
                    n.push([x, y]);
                });
                n.point = d.point;
                shapes.push(n);
            }
        });

        return shapes;
    }

    var force = d3.layout.force()
    .charge(-1000)
    .friction(0.3)
    .linkDistance( function(d) { 
        // TODO: this should be normalized to the cluster's largest edge probability
        return 300*Math.sqrt(d.probability);
    })
    .size([width, height]);

    var damper = 0.1;
    force.on('tick', function(e) {
        node.attr('transform', function(d) { 
            if(d.index==0){
                // according to: http://stackoverflow.com/a/9684465
                d.x = d.x + (width/2 - d.x) * (damper + 0.71) * e.alpha;
                d.y = d.y + (height/2 - d.y) * (damper + 0.71) * e.alpha;
            }
            return 'translate('+d.x+','+d.y+')'; 
        })
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
    .style("stroke-width", function(d) { return Math.sqrt(d.probability); });

    node = svg.selectAll('.node')
    .data( graph.nodes )
    .enter().append('g')

    node.append('circle')
    .attr('r', 20)
    .attr('fill', colorByGroup)
    .attr('fill-opacity', 0.5);

    node.append('circle')
    .attr('r', 19)
    .attr('fill', colorByGroup)
    .attr('fill-opacity', 0.5)
    .attr('stroke', 'black');

    force
    .nodes( graph.nodes )
    .links( graph.links )
    .start();
}

function condenseData( theData ) {
    var cluster_markov = {}
    for( var p1 in theData.chains ) {
        for( var p2 in theData.chains[p1] ) {
            var p1_cluster_id = theData.clusters[p1];
            var p2_cluster_id = theData.clusters[p2];
            if( p1_cluster_id != p2_cluster_id ) { // if inter-cluster connection 
                if( cluster_markov[p1_cluster_id] === undefined ) {
                    cluster_markov[p1_cluster_id] = {};
                }
                if( cluster_markov[p1_cluster_id][p2_cluster_id] === undefined ) {
                    cluster_markov[p1_cluster_id][p2_cluster_id] = 0.50; 
                }
                //cluster_markov[p1_cluster_id][p2_cluster_id] += theData.chains[p1][p2];
            }
        } 
    }

    return {
        chains: cluster_markov
    }
}

function linkData( theData, cluster_id ) {
    var nodeList = findNodes( theData.chains );
    var linkList = findLinks( theData.chains, nodeList );

    function inClusterFilter( key ) {
        if( cluster_id ) 
            return theData.clusters[key] == cluster_id;
        else
            return true;
    }

    function findNodes( chains, clusters ) {
        var result = [];
        for( var key in chains ) {
            var index = result.indexOf( key );
            if( index < 0 ) {
                if(inClusterFilter(key)) {
                    result.push( key );
                }
            }
        }
        return result;
    }

    function findLinks( chains, nodeList ) {
        var result = [];
        for( var key in chains ) {
            var connectedDict = chains[key];
            if(inClusterFilter(key)) {
                for( var connectedKey in connectedDict ) {
                    if(inClusterFilter(connectedKey)) { 
                        var sourceIndex = nodeList.indexOf( key );
                        var targetIndex = nodeList.indexOf( connectedKey );
                        var probability = connectedDict[connectedKey];
                        var link = {
                            source: sourceIndex,
                            target: targetIndex,
                            probability: probability, 
                        }
                        result.push( link );
                    }
                }
            }
        }
        return result;
    }

    nodeList = nodeList.map( function(item, index) {
        return {
            name: item,
            group: cluster_id ? cluster_id : undefined,
        }
    });

    var result = {
        nodes: nodeList,
        links: linkList,
        clusters: theData.clusters ? theData.clusters : undefined,
    }

    return result;
}

