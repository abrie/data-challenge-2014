"use strict";

$( document ).ready( main );

function generateSvgElement(id) {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute('id', id);
    svg.setAttribute('preserveAspectRatio',"xMidYMid slice");
    svg.setAttribute('viewbox','0 0 1000 1000');
    svg.setAttributeNS(
        "http://www.w3.org/2000/xmlns/",
        "xmlns:xlink",
        "http://www.w3.org/1999/xlink");

    return $(svg);
}

function main() {
    $.ajax({
        url: "data/results.json",
        dataType: "json",
    })
    .done(function( data ) {
        var svgElement = generateSvgElement("main-svg");
        $("#graph").append( svgElement );
        displayData( data , "#main-svg" );
    })
    .error(function(jqXHR, textStatus, errorThrown) { 
        console.log('error retrieving data:', errorThrown); 
    })
}

function displayData( raw_data, element_id ) {
    var graphData = buildGraphData( raw_data.cluster_chains, raw_data.weights );
    var g = new dagreD3.Digraph();

    var colorSelector = d3.scale.category20();
    graphData.nodes.forEach( function(node) {
        g.addNode(node.name, { 
            useFunction: function( parent_node) {
                var clusterGraphData = buildGraphData( raw_data.chains, raw_data.weights, raw_data.clusters, node.name );
                createClusterGraph( clusterGraphData, parent_node, colorSelector );
            }
        });
    });

    graphData.links.forEach( function(edge) {
        var source = graphData.nodes[edge.source].name;
        var target = graphData.nodes[edge.target].name;
        var weight = edge.weight;
        var appearance = { style: 'stroke-width: 1px;' };
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

    var data = {name:'root', children:graph.nodes};
    var pack = d3.layout.pack()
        .value( function(d) { 
            if( d.params ) {
                return d.params.weight*d.params.hits;
            }
            else {
                return 10;
            }
        })
        .size([50,50])
        .nodes(data);

    pack.shift();

    svg.selectAll('circles')
    .data(pack)
    .enter().append('svg:circle')
    .attr('cx', function(d) { return d.x; })
    .attr('cy', function(d) { return d.y; })
    .attr('r', function(d) { return d.r; })
    .attr('fill', 'white')
    .attr('stroke', 'grey');

    // center the pack
    var bbox = svg[0][0].getBBox();
    var cx = bbox.width / 2 + bbox.x;
    var cy = bbox.height /2 + bbox.y;
    svg.attr("transform","translate("+-cx+","+-cy+")");
}

function buildGraphData( chain_dict, weight_map, cluster_map, cluster_id ) {

    function inClusterFilter( key ) {
        if( cluster_map !== undefined && cluster_id !== undefined ) 
            return cluster_map[key] == cluster_id;
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
                        var params = connectedDict[connectedKey];
                        var link = {
                            source: sourceIndex,
                            target: targetIndex,
                            hits: params.hits,
                            weight: params.weight, 
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
                params: weight_map[item], 
                group: cluster_id ? cluster_id : undefined,
            }
        });
    }

    var nodeList = buildNodeList( chain_dict );

    return {
        nodes: mapNodeList( nodeList ),
        links: buildLinkList( chain_dict, nodeList ),
    }
}

