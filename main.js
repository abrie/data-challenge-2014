"use strict";

$( document ).ready( main );

var VIEWBOX = {
    "min_x":0,
    "min_y":0,
    "width":2000,
    "height":2000,
    "str": function() {
        return [
            this.min_x,
            this.min_y,
            this.width,
            this.height
        ].join(" ")},
    "midpoint": function() {
        return "translate(" + this.width/2 + "," + this.height/2 + ")";
    }
}

function generateSvgElement(id) {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute('id', id);
    svg.setAttribute('preserveAspectRatio',"xMidYMid slice");
    svg.setAttribute('viewBox',VIEWBOX.str());
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

function build_runner( model ) {
    var table = {};
    for(var k in model) {
        var list = [];
        for( var k2 in model[k] ) {
            list.push({
                event: k2,
                weight: model[k][k2].weight
            });
        }
        list.sort( function(a,b) {
            if( a.weight > b.weight )
                return 1;
            if( a.weight < b.weight )
                return -1;
            return 0;
        });
        table[k] = list;
    }

    return table;
}

function next(current, p, table) {
    console.log(p);
    var list = table[current];
    var index = 0;
    while( index < list.length-1 ) {
        if( p >= list[index].weight && p < list[index+1].weight ) {
            return list[index].event
        }
        index++;
    }
    return list[list.length-1].event;
}

function displayData( raw_data, selector ) {

    var l = build_runner( raw_data.event_model );
    var event = '~';
    for( var i = 0; i < 10; i++ ) {
        console.log(event);
        event = next(event, Math.random(), l);
    }

    var radius = 325;
    var cluster = d3.layout.cluster()
        .size([360, radius])
        .sort( function(a,b) { return d3.ascending(a.value, b.value) } )

    var clusters = [];
    for( var cluster_id in raw_data.cluster_degrees ) {
        var cluster_data = buildGraphData( raw_data.event_model, raw_data.node_degrees, cluster_id )
        clusters.push({
            "name":cluster_id,
            "value":raw_data.cluster_degrees[cluster_id].indegree + raw_data.cluster_degrees[cluster_id].outdegree,
            "children":cluster_data.nodes
        });
    }

    var node_data = {
        "name":"root", 
        "value":0,
        children: clusters
    };

    var nodes = cluster.nodes( node_data );
    var node_name_map = {}
    nodes.forEach( function(node) {
        node_name_map[node.name] = node;
    });

    var links = [];
    for(var k in raw_data.event_model) {
        for(var k2 in raw_data.event_model[k] ) {
            links.push({
                source:node_name_map[k],
                target:node_name_map[k2]
            });
        } 
    }

    var line = d3.svg.line.radial()
        .interpolate("bundle")
        .tension(.15)
        .radius(function(d) { 
            return d.y; 
        })
        .angle(function(d) { 
            return d.x / 180 * Math.PI; 
        });

    var svg = d3.select(selector)
        .append("g")
        .attr("transform", VIEWBOX.midpoint());

    var bundle = d3.layout.bundle();
    var link = svg.append("g")
        .selectAll(".link")
        .data( bundle(links) )
        .enter().append("path")
        .attr("class","link")
        .attr("d", line);

    d3.select("input[type=range]").on("change", function() {
        line.tension(this.value / 100);
        link.attr("d", line );
    });

    var node = svg.append("g").selectAll(".node")
        .data(nodes)
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", function(d) { 
            return "rotate(" + (d.x - 90) + ")translate(" + d.y + ")"; 
        })
        .append("text")
        .attr("dx", function(d) { 
            return d.x < 180 ? 8 : -8; 
        })
        .attr("dy", "0.5")
        .attr("text-anchor", function(d) { 
            return d.x < 180 ? "start" : "end";
        })
        .attr("font-size", "30")
        .attr("transform", function(d) { 
            return d.x < 180 ? null : "rotate(180)";
        })
        .text(function(d) { 
            return d.name + "(" + d.value + ")"; 
        });
}

function buildGraphData(model, node_degrees, cluster_id) {
    function inClusterFilter( key ) {
        if( node_degrees !== undefined && cluster_id !== undefined ) 
            return node_degrees[key].cluster == cluster_id;
        else
            return true;
    }

    function buildNodeList(model) {
        var result = [];
        for( var key in model ) {
            var index = result.indexOf( key );
            if( index < 0 ) {
                if(inClusterFilter(key)) {
                    result.push( key );
                }
            }
        }

        return result.map( function(key) { 
            return { 
                "name":key,
                "value":node_degrees[key].indegree+node_degrees[key].outdegree
            } 
        });
    }

    function buildLinkList(model) {
        var result = [];
        for( var key in model ) {
            var connectedDict = model[key];
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
        nodes: buildNodeList( model ), 
        links: buildLinkList( model ),
    }
}
