"use strict";

$( document ).ready( main );

var VIEWBOX = { x:0, y:0, width:300, height:300 };

function generateSvgElement(id) {
    // as per http://stackoverflow.com/a/8215105
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute('id', id);
    svg.setAttribute('preserveAspectRatio',"xMidYMid slice");
    svg.setAttribute('viewbox',VIEWBOX.x + ' ' + VIEWBOX.y + ' ' + VIEWBOX.width + ' ' + VIEWBOX.height);
    svg.setAttributeNS(
        "http://www.w3.org/2000/xmlns/",
        "xmlns:xlink",
        "http://www.w3.org/1999/xlink");

    return $(svg);
}

function main() {
    $.getJSON("data/results.json", function( raw_data ) {
        var svgElement = generateSvgElement("main-svg");
        $("#graph").append( svgElement );
        displayData( raw_data , "#main-svg" );
    }); 
}

function displayData( raw_data, element_id ) {
    var graphData = buildGraphData( condenseData(raw_data) );
    var g = new dagreD3.Digraph();

    var colorSelector = d3.scale.category20();
    graphData.nodes.forEach( function(node) {
        g.addNode(node.name, { 
            //useFunction: function(d) { console.log("i've been called:", d, d3.select(g)); }
            label: 'testing',
            useFunction: function(d) {
                createClusterGraph( buildGraphData(raw_data, node.name), d, colorSelector );
            }
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
    renderer.zoom(false);

    var layout = dagreD3.layout()
        .nodeSep(10)
        .edgeSep(25)
        .rankSep(30)
        .rankDir("TB");
    
    var element = d3.select( element_id );
    var rendered_layout = renderer.layout(layout).run(g, element);

    function zoomToFit() {
        var width = rendered_layout.graph().width;
        var height = rendered_layout.graph().height;
        
        var container = $(element_id);
        var zoomFactor = 1.0;
        if( width > height ) {
            zoomFactor = container.width() / width;
        }
        else {
            zoomFactor = container.height() / height;
        }

        var zoom = d3.select("g.zoom", element);
        zoom.attr("transform","scale("+zoomFactor+")");
    }

    zoomToFit();
    d3.select(window).on('resize', zoomToFit);
}

function createClusterGraph( graph, root, colorSelector ) {
    function name(d) { return d.name; }

    function colorByGroup(d) { 
        return colorSelector( d.name ) ; 
    }

    var svg = root.append("g");

    svg.append('circle')
    .attr('r', 20)
    .attr('fill', colorByGroup)
    .attr('fill-opacity', 0.5);

    svg.append('circle')
    .attr('cx', 20)
    .attr('cy', 20)
    .attr('r', 20)
    .attr('fill', colorByGroup)
    .attr('fill-opacity', 0.5);

    svg.append('circle')
    .attr('r', 19)
    .attr('fill', colorByGroup)
    .attr('fill-opacity', 0.5)
    .attr('stroke', 'black');
}

function condenseData( rawData ) {
    var chains = {}
    for( var p1 in rawData.chains ) {
        for( var p2 in rawData.chains[p1] ) {
            var p1_cluster_id = rawData.clusters[p1];
            var p2_cluster_id = rawData.clusters[p2];
            if( p1_cluster_id != p2_cluster_id ) { // if inter-cluster connection 
                if( chains[p1_cluster_id] === undefined ) {
                    chains[p1_cluster_id] = {};
                }
                if( chains[p1_cluster_id][p2_cluster_id] === undefined ) {
                    chains[p1_cluster_id][p2_cluster_id] = 0.50; 
                }
                //chains[p1_cluster_id][p2_cluster_id] += rawData.chains[p1][p2];
            }
        } 
    }

    return {
        chains: chains
    }
}

function buildGraphData( rawData, cluster_id ) {

    function inClusterFilter( key ) {
        if( cluster_id ) 
            return rawData.clusters[key] == cluster_id;
        else
            return true;
    }

    function buildNodeList( chains, clusters ) {
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

    function buildLinkList( chains, nodeList ) {
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

    function mapNodeList( list ) {
        return list.map( function(item, index) {
            return {
                name: item,
                group: cluster_id ? cluster_id : undefined,
            }
        });
    }

    var nodeList = buildNodeList( rawData.chains );

    return {
        nodes: mapNodeList( nodeList ),
        links: buildLinkList( rawData.chains, nodeList ),
    }
}

