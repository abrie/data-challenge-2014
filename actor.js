"use strict";

$( document ).ready( main );

function ViewBox(width, height, aspect) {
    return { 
        "min_x":-width/2,
        "min_y":-height/2,
        "width":width,
        "height":height,
        "aspect":aspect,
        "attr": function() {
            return [
                this.min_x,
                this.min_y,
                this.width,
                this.height
            ].join(" ")},
    }
}

function generateSvgElement(id, viewBox) {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute('id', id);
    svg.setAttribute('preserveAspectRatio',viewBox.aspect);
    svg.setAttribute('viewBox',viewBox.attr());
    svg.setAttributeNS(
        "http://www.w3.org/2000/xmlns/",
        "xmlns:xlink",
        "http://www.w3.org/1999/xlink");

    return $(svg);
}

function main() {
    get_and_display("data/actor/results.json", "container");
}

function get_and_display(url, id) {
    $.ajax({
        url: url,
        dataType: "json",
    })
    .done(function( d ) {
        generateDisplay(d, id );
    })
    .error(function(jqXHR, textStatus, errorThrown) { 
        console.log('error retrieving data:', errorThrown); 
    })
}

function generateDisplay(data, id) {
    var svgElement = generateSvgElement( "svg-"+id,
        new ViewBox(3000,3000, "xMidYMid meet"));
    $("#"+id).append( svgElement );
    var selector = "#svg-"+id;
    displayModel( data.model, data.state, selector );
}

function displayModel( data, state, selector ) {
    var svg = d3.select(selector)
        .append("g")
        .call( d3.behavior.zoom().scaleExtent([1,8]).on("zoom",zoom))
        .append("g").attr("class","overlay");

    function zoom() {
        svg.attr("transform", 
                 "translate(" + d3.event.translate + ") scale(" + d3.event.scale + ")");
    }

    var nodeGroup = svg.append("g").attr("class","node-group");
    var linkGroup_a = svg.append("g").attr("class","link-group");
    var linkGroup_b = svg.append("g").attr("class","link-group");

    var radius = 350;

    var clusters = [];
    for( var cluster_id in data.cluster_degrees ) {
        var indegree = data.cluster_degrees[cluster_id].indegree;
        var outdegree = data.cluster_degrees[cluster_id].outdegree;
        clusters.push({
            "name": cluster_id,
            "degree": indegree - outdegree,
            "children": getNodesForCluster( data, cluster_id )
        });
    }

    function sumInWeight(name) {
        var sum = 0;
        for(var k in data.event_model) {
            var event = data.event_model[k][name];
            sum += event ? event.weight : 0;
        }
        return sum;
    }

    var clusterLayout = d3.layout.cluster()
        .size([360, radius])
        .sort( function(a,b) {
            var a = sumInWeight(a.name);
            var b = sumInWeight(b.name);
            return d3.descending(a, b)
        })

    var nodes = clusterLayout.nodes( {
            "name":"root", 
            "degree":0,
            children: clusters
        });

    var node_names = {}
    nodes.forEach( function(node) {
        node_names[node.name] = node;
    });

    function getLinks(minWeight,maxWeight) {
        var result = [];
        for(var k in data.event_model) {
            for(var k2 in data.event_model[k] ) {
                var weight = data.event_model[k][k2].weight;
                if( weight >= minWeight && weight < maxWeight ) {
                    var source = node_names[k];
                    var target = node_names[k2];
                    result.push({
                        source:source,
                        target:target,
                    });
                }
            } 
        }
        return result;
    }


    var line = d3.svg.line.radial()
        .interpolate("bundle")
        .tension(0.35)
        .radius(function(d) { 
            return d.y; 
        })
        .angle(function(d) { 
            return d.x / 180 * Math.PI; 
        });

    var bundle = d3.layout.bundle();
    var linkColorScale = d3.scale.category10();

    function populationDomain() {
        var result = [];
        for(var k in state) {
            result.push(state[k].hits)
        }

        var sorted = result.sort(function(a,b) { 
            if(a<b) return -1;
            if(a>b) return 1;
            return 0
        });

        return [sorted[0], sorted[sorted.length-1]];
    }

    var populationScale = d3.scale.log().domain(populationDomain()).range([1,180]);

    function getScaledPopulation(name) {
        var event = state[name];
        if(event) {
            return populationScale(event.hits);
        }
        else {
            return 1;
        }
    }

    function weightsList() {
        var set = {};
        for(var k in data.event_model) {
            for(var k2 in data.event_model[k]) {
                var weight = data.event_model[k][k2].weight;
                set[weight] = true;
            }
        }
        var result = [];
        for(var k in set) {
            result.push(parseFloat(k));
        }

        return result;
    }

    function drawLinks(linkGroup, linkCollection, linkClass, opacityScale) { 
        return linkGroup.selectAll(".link")
            .data( bundle(linkCollection) )
            .enter().append("path")
            .attr("class", linkClass)  
            .style("stroke-linecap","rounded")
            .style("opacity", function(d) {
                var source_state = d[0].name
                var target_state = d[d.length-1].name
                var weight = data.event_model[source_state][target_state].weight;
                return opacityScale(weight);  
            })
            .style("stroke", function(d) {
                var source_state = d[0].name
                var source_cluster = data.clusters[source_state]; 
                return linkColorScale(source_cluster);
            })
            .style("stroke-width", function(d) {
                var source_state = d[0].name
                var target_state = d[d.length-1].name
                var weight = data.event_model[source_state][target_state].weight;
                return linkWidthScale(weight);  
            })
            .attr("d", line);
    }

    var linkWidthScale = d3.scale.linear().domain(weightsList()).range([1,7]);

    var links_a = getLinks(0,0.30);
    var opacityScale_a = d3.scale.linear().domain(weightsList()).range([0.3,0.5]);
    var drawnLink_a = drawLinks(linkGroup_a, links_a, "link-a", opacityScale_a);

    var links_b = getLinks(0.30,1.0);
    var opacityScale_b = d3.scale.linear().domain(weightsList()).range([0.5,0.9]);
    var drawnLink_b = drawLinks(linkGroup_b, links_b, "link-b", opacityScale_b);

    $(selector+" input[type=range]").on("change", function() {
        line.tension(this.value / 100);
        drawnLink_a.attr("d", line );
        drawnLink_b.attr("d", line );
    });

    var node = nodeGroup.selectAll(".node")
        .data(nodes)
        .enter().append("g")
        .attr("class", "node");

    var font_size = 30;
    var label = node.filter( function(d) { return d.depth > 1})
        .append("g")
        .attr("transform", function(d) { 
            var t = d3.svg.transform()
                .rotate(d.x-90)
                .translate(d.y, 0);
            return t();
        });

    var box = label.append("rect")
        .attr("height",8 )
        .attr("width", function(d) { 
            return getScaledPopulation(d.name);
        })
        .attr("transform", function(d) {
            var t = d3.svg.transform()
                .translate(0,-font_size/4);
            return t();
        })
        .style("fill", function(d) {
            var source_state = d.name
            var source_cluster = data.clusters[source_state]; 
            return linkColorScale(source_cluster);
        })
        .style("opacity", "0.80")

    var text = label.append("text")
        .attr("class","node-text")
        .attr("dx", function(d) {
            var offset = 20;
            if( d.x > 180 && d.x < 360 ) {
                offset = -20;
            }
            return offset;
        })
        .style("font-size", font_size)
        .attr("alignment-baseline", function(d) {
            var alignment = "before-edge";
            if( d.x > 180 && d.x < 360 ) {
                alignment = "auto";
            }
            return alignment;
        })
        .attr("text-anchor", function(d) {
            if( d.x > 180 && d.x < 360 ) {
                return "end";
            }
            else {
                return "start";
            }
        })
        .attr("transform", function(d) {
            var angle = 0;
            if( d.x > 180 && d.x < 360 ) {
               angle = 180 
            }
            var t = d3.svg.transform()
                .translate(getScaledPopulation(d.name),0)
                .rotate(angle);
            return t();
        })
        .text(function(d) { 
            return d.name; 
        });
}

function getNodesForCluster(data, cluster_id) {
    var setCollection = {};
    for( var key in data.event_model ) {
        if( data.clusters[key] !== cluster_id ) {
           continue;
        }
        else {
            var indegree = data.node_degrees[key].indegree;
            var outdegree = data.node_degrees[key].outdegree;
            setCollection[key] = { 
                "name": key,
                "degree": indegree - outdegree
            } 
        }
    }

    var result = [];
    for( var key in setCollection ) {
        result.push(setCollection[key]);
    } 

    return result;
}
