function Main() {
    'use strict';

function go(url, container_selector) {
    load_json( url, function(result) { 
        generateDisplay(result, container_selector);
    });
}

function generateDisplay(data, container_selector) {
    var viewBox = new ViewBox(2000,2000, "xMidYMid meet");
    var svgElement = generateSvgElement(viewBox);
    $(container_selector).append( svgElement );
    generateIllustration( data.model, data.state, svgElement );
}

function generateIllustration( data, populations, svgElement ) {
    var svg = d3.select(svgElement);

    svg = makeZoomPan(svg);

    var nodeGroup = svg.append("g").attr("class","node-group");
    var linkGroup_a = svg.append("g").attr("class","link-group");
    var linkGroup_b = svg.append("g").attr("class","link-group");

    var radius = 350;
    var clusterLayout = d3.layout.cluster()
        .size([360, radius])
        .sort( function(a,b) {
            var a_sum = sumIncidentEdgeWeights(data.event_model, a.name);
            var b_sum = sumIncidentEdgeWeights(data.event_model, b.name);
            return d3.descending(a_sum, b_sum);
        });

    var hierarchy = getClusterHierarchy(data);
    var nodes = clusterLayout.nodes(hierarchy) ;
    var nameNodeMap = new NodeNameLookupFunction(nodes);

    var line = d3.svg.line.radial()
        .interpolate("bundle")
        .tension( getTensionSliderValue() )
        .radius(function(d) { 
            return d.y; 
        })
        .angle(function(d) { 
            return d.x / 180 * Math.PI; 
        });

    var bundle = d3.layout.bundle();
    var linkColorScale = d3.scale.category10();

    var totalPopulation = 0;
    function populationDomain() {
        var max = 1;
        for(var k in populations) {
            var population = populations[k].hits;
            totalPopulation  += population;
            max = population > max ? population : max;
        }

        return [1, max];
    }

    var populationScale = d3.scale.log()
        .domain( populationDomain() )
        .range([1,220]);

    function getScaledPopulation(name) {
        var event = populations[name];
        if(event) {
            return populationScale(event.hits);
        }
        else {
            return 1;
        }
    }

    function getScaledStationaryPopulation(name) {
        var event = data.stationary_model[name];
        if(event) {
            var stationary = data.stationary_model[name]*totalPopulation;
            var scaled =  populationScale(stationary);
            return scaled;
        }
        else {
            return 1;
        }
    }

    function getTransition(source, target) {
        return data.event_model[source][target];
    }

    function getCluster(nodeName) {
        return data.clusters[nodeName]; 
    }

    var linkWidthScale = d3.scale.linear()
        .domain(getWeightDomain()).range([1,7]);

    function drawLinks(linkGroup, linkCollection, linkClass, opacityScale) { 
        return linkGroup.selectAll(".link")
            .data( bundle(linkCollection) )
            .enter().append("path")
            .attr("class", linkClass)  
            .style("stroke-linecap","rounded")
            .style("opacity", function(d) {
                var source = d[0].name;
                var target = d[d.length-1].name;
                var weight = getTransition(source, target).weight;
                return opacityScale(weight);  
            })
            .style("stroke", function(d) {
                var source = d[0].name;
                return linkColorScale( getCluster(source) );
            })
            .style("stroke-width", function(d) {
                var source = d[0].name;
                var target = d[d.length-1].name;
                var weight = getTransition(source, target).weight;
                return linkWidthScale(weight);  
            })
            .attr("d", line);
    }

    function getWeightDomain(range) {
        var set = {"0":true};
        for(var event_a in data.event_model) {
            for(var event_b in data.event_model[event_a]) {
                var weight = getTransition(event_a, event_b).weight;
                if( range ) {
                    if( weight >= range.min && weight < range.max ) {
                        set[weight] = true;
                    }
                }
                else {
                    set[weight] = true;
                }
            }
        }

        var result = [];
        for(var weightString in set) {
            result.push( parseFloat(weightString) );
        }

        return result;
    }

    function drawEdges( weightRange, linkGroup, linkClass, opacityRange ) {
        var opacityScale = d3.scale.linear()
            .domain(getWeightDomain(weightRange))
            .range(opacityRange);
        var links = getLinks(data.event_model, nameNodeMap, weightRange);
        return drawLinks(linkGroup, links, linkClass, opacityScale);
    }

    // Edges are grouped into "high probability" and "low probability" in order to
    // control their SVG layering.
    var lowEdges = drawEdges({min:0, max:0.30}, linkGroup_a, "link-a", [0.2,0.3]);
    var highEdges = drawEdges({min:0.30, max:1.0}, linkGroup_b, "link-b", [0.7,0.9]); 

    function getTensionSliderValue() {
        var slider = d3.select("input[name='tension']")[0][0];
        return slider.value;
    }

    d3.select("input[name='tension']").on("change", function() {
        line.tension(this.value);
        lowEdges.attr("d", line );
        highEdges.attr("d", line );
    });

    var node = nodeGroup.selectAll(".node")
        .data(nodes)
        .enter().append("g")
        .attr("class", "node");

    var font_size = 30;
    var label = node.filter( function(d) { return d.depth > 1;})
        .append("g")
        .attr("transform", function(d) { 
            var t = d3.svg.transform()
                .rotate(d.x-90)
                .translate(d.y, 0);
            return t();
        });

    var sbox = label.append("rect")
        .attr("height",8 )
        .attr("width", function(d) { 

            return getScaledStationaryPopulation(d.name);
        })
        .attr("transform", function(d) {
            var t = d3.svg.transform()
                .translate(0,font_size/4);
            return t();
        })
        .style("fill", function(d) {
            var source = d.name;
            var source_cluster = data.clusters[source]; 
            return "black";// linkColorScale(source_cluster);
        })
        .style("opacity", "0.80");

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
            var source = d.name;
            var source_cluster = data.clusters[source]; 
            return linkColorScale(source_cluster);
        })
        .style("opacity", "0.80");

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
               angle = 180; 
            }
            var t = d3.svg.transform()
                .translate(getScaledPopulation(d.name),0)
                .rotate(angle);
            return t();
        })
        .text(function(d) { 
            if( d.name === '~' ) {
                if( d.x > 180 && d.x < 360 ) {
                    return "start -->";
                }
                else {
                    return "<-- start";
                }
            }
            else {
                return d.name; 
            }
        });
}

function getLinks( model, nameNodeMap, weightRange ) {
    var result = [];
    for(var k in model) {
        for(var k2 in model[k] ) {
            var weight = model[k][k2].weight;
            if( weight >= weightRange.min && weight < weightRange.max ) {
                var source = nameNodeMap(k);
                var target = nameNodeMap(k2);
                result.push({
                    source:source,
                    target:target,
                });
            }
        } 
    }
    return result;
}

function sumIncidentEdgeWeights( model, node_name ) {
    var sum = 0;
    for(var k in model) {
        var event = model[k][node_name];
        sum += event ? event.weight : 0;
    }
    return sum;
}

function NodeNameLookupFunction(nodes) {
    var node_names = {};
    nodes.forEach( function(node) {
        node_names[node.name] = node;
    });

    return function(node) {
        return node_names[node];
    };
}

function getClusterHierarchy(data) {
    var hierarchy = [];
    for( var cluster_id in data.cluster_degrees ) {
        hierarchy.push({
            "name": cluster_id,
            "children": getClusterChildren( data, cluster_id )
        });
    }

    return {
        "name":"root", 
        children: hierarchy
    };
}

function getClusterChildren(data, cluster_id) {
    var setCollection = {};
    for( var key in data.node_degrees ) {
        if( data.clusters[key] === cluster_id ) {
            setCollection[key] = { "name": key };
        }
    }

    var result = [];
    for( var uniqueKey in setCollection ) {
        result.push(setCollection[uniqueKey]);
    } 

    return result;
}

function ViewBox(width, height, aspect) {
    return { 
        "min_x":-width/2,
        "min_y":-height/2,
        "width":width,
        "height":height,
        "preserveAspectRatio": function() {
            return aspect;
        },
        "viewBox": function() {
            return [
                this.min_x,
                this.min_y,
                this.width,
                this.height
            ].join(" ");},
    };
}

function generateSvgElement(viewBox) {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute('preserveAspectRatio', viewBox.preserveAspectRatio());
    svg.setAttribute('viewBox',viewBox.viewBox());
    svg.setAttributeNS(
        "http://www.w3.org/2000/xmlns/",
        "xmlns:xlink",
        "http://www.w3.org/1999/xlink");

    return svg;
}

function makeZoomPan( svg ) {
    var zoomGroup = svg.append("g")
        .attr("class","zoom-group");
    var zoomTarget = zoomGroup.append("g")
        .attr("class","zoom-target");
    var zoomBehaviour = d3.behavior.zoom()
        .scaleExtent([0.5,8])
        .on("zoom",zoom);

    function zoom() {
        var translate = "translate(" + d3.event.translate + ")"; 
        var scale = "scale(" + d3.event.scale + ")";
        zoomTarget.attr("transform", translate + " " + scale); 
    }

    zoomGroup.call( zoomBehaviour );
    return zoomTarget;
}

function load_json(url, callback) {
    $.ajax({
        url: url,
        dataType: "json",
    })
    .done(function( d ) {
        callback(d);
    })
    .error(function(jqXHR, textStatus, errorThrown) { 
        console.log('error retrieving data:', errorThrown); 
    });
}

return {go:go};
}
