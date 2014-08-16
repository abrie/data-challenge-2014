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

function displayData( raw_data, selector ) {
    var outter_radius = 300;
    var inner_radius = 250;
    var cluster = d3.layout.cluster()
        .size([360, inner_radius])
        .value( function(d) { return 10; } ); 

    var clusters = [];
    for( var cluster_id in raw_data.cluster_degrees ) {
        var cluster_data = buildGraphData( raw_data.chains, raw_data.node_degrees, cluster_id )
        clusters.push({"name":cluster_id, "children":cluster_data.nodes});
    }

    var node_data = {
        "root":"top", 
        children: clusters
    };

    var nodes = cluster.nodes( node_data );
    var node_name_map = {}
    nodes.forEach( function(node) {
        node_name_map[node.name] = node;
    });
    console.log(node_name_map);

    var links = [];
    for(var k in raw_data.chains) {
        for(var k2 in raw_data.chains[k] ) {
            links.push({source:node_name_map[k], target:node_name_map[k2]});
        } 
    }

    var bundle = d3.layout.bundle();
    var line = d3.svg.line.radial()
    .interpolate("bundle")
    .tension(.01)
    .radius(function(d) { return d.y; })
    .angle(function(d) { return d.x / 180 * Math.PI; });

    var splines = bundle(links);

    var svg = d3.select(selector)
        .attr("width", outter_radius*2)
        .attr("height", outter_radius*2)
        .append("g")
        .attr("transform", "translate(" + outter_radius + "," + outter_radius + ")" );

    var link = svg.append("g").selectAll(".link")
        .data( links )
        .enter().append("path")
        .attr("class","link")
        .attr("d", function(d,i) { return line(splines[i]); } );

    var node = svg.append("g").selectAll(".node")
        .data(nodes)
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", function(d) { return "rotate(" + (d.x - 90) + ")translate(" + d.y + ")"; })
        .append("text")
        .attr("dx", function(d) { return d.x < 180 ? 8 : -8; })
        .attr("dy", ".31em")
        .attr("text-anchor", function(d) { return d.x < 180 ? "start" : "end"; })
        .attr("transform", function(d) { return d.x < 180 ? null : "rotate(180)"; })
        .text(function(d) { return d.name; });
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
    .attr('fill', function(d) { return colorSelector(d.name); })
    .attr('stroke', 'grey');

    // center the pack
    var bbox = svg[0][0].getBBox();
    var cx = bbox.width / 2 + bbox.x;
    var cy = bbox.height /2 + bbox.y;
    svg.attr("transform","translate("+-cx+","+-cy+")");
}

function buildGraphData( chain_dict, node_degrees, cluster_id ) {
    function inClusterFilter( key ) {
        if( node_degrees !== undefined && cluster_id !== undefined ) 
            return node_degrees[key].cluster == cluster_id;
        else
            return true;
    }

    function buildNodeList( chains ) {
        var result = [];
        for( var key in chains ) {
            var index = result.indexOf( key );
            if( index < 0 ) {
                if(inClusterFilter(key)) {
                    result.push( key );
                }
            }
        }

        return result.map( function(key) { 
            return {parent:"top", name:key} 
        });
    }

    function buildLinkList( chains ) {
        var result = [];
        for( var key in chains ) {
            var connectedDict = chains[key];
            if(inClusterFilter(key)) {
                for( var connectedKey in connectedDict ) {
                    if(inClusterFilter(connectedKey)) { 
                        var source = key;
                        var target = connectedKey;
                        var link = {
                            source: key,
                            target: connectedKey,
                        }
                        result.push( link );
                    }
                }
            }
        }
        return result;
    }

    return {
        nodes: buildNodeList( chain_dict ), 
        links: buildLinkList( chain_dict ),
    }
}

