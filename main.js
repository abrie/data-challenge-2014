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
        url: "data/latest/results.json",
        dataType: "json",
    })
    .done(function( data ) {
        var svgElement = generateSvgElement("main-svg");
        $("#graph").append( svgElement );
        displayData( data.model , "#main-svg" );
        console.log( data.state );
    })
    .error(function(jqXHR, textStatus, errorThrown) { 
        console.log('error retrieving data:', errorThrown); 
    })
}

function displayData( raw_data, selector ) {
    var radius = 300;
    var cluster = d3.layout.cluster()
        .size([360, radius])
        .sort( function(a,b) { return d3.ascending(a.value, b.value) } )

    var clusters = [];
    for( var cluster_id in raw_data.cluster_degrees ) {
        clusters.push({
            "name":cluster_id,
            "value":raw_data.cluster_degrees[cluster_id].indegree + raw_data.cluster_degrees[cluster_id].outdegree,
            "children": getNodesForCluster( raw_data, cluster_id )
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
        .tension(0.85)
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
    var linkColorScale = d3.scale.category10();
    var linkWidthScale = d3.scale.pow().range([0.0,10]);
    var link = svg.append("g")
        .selectAll(".link")
        .data( bundle(links) )
        .enter().append("path")
        .attr("class","link")  
        .style("stroke", function(d) {
            var source_state = d[0].name
            var source_cluster = raw_data.clusters[source_state]; 
            return linkColorScale(source_cluster);
        })
        .style("stroke-width", function(d) {
            var source_state = d[0].name
            var target_state = d[d.length-1].name
            var weight = raw_data.event_model[source_state][target_state].weight;
            return linkWidthScale(weight);  
        })
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
            if(d.depth === 2) {
                return d.name + "(" + d.value + ")"; 
            }
        });
}

function getNodesForCluster(data, cluster_id) {
    var setCollection = {};
    for( var key in data.event_model ) {
        if( data.clusters[key] !== cluster_id ) {
           continue;
        }
        else if( key === '~' ) {
            setCollection[key] = { 
                "name": key,
                "value": 0 
            } 
        }
        else {
            setCollection[key] = { 
                "name": key,
                "value": data.node_degrees[key].indegree - data.node_degrees[key].outdegree
            } 
        }
    }

    var result = [];
    for( var key in setCollection ) {
        result.push(setCollection[key]);
    } 

    return result;
}
