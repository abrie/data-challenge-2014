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

function CornerViewBox(width, height, aspect) {
    return { 
        "min_x":0,
        "min_y":0,
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
    $.ajax({
        url: "data/latest/results.json",
        dataType: "json",
    })
    .done(function( data ) {
        function a() {
            var svgElement = generateSvgElement( "main-svg",
                new ViewBox(1450,1450, "xMidYMid meet"));
            $("#graph").append( svgElement );
            displayModel( data.model, data.state, "#main-svg" );
        }
        
        function b() {
            var svgElement_b = generateSvgElement( "main-svg",
                new CornerViewBox(1450,1450, "xMinYMin meet"));
            $("#graph").append( svgElement_b );
            displayTimes( data.times , "#main-svg" );
        }

        a();
    })
    .error(function(jqXHR, textStatus, errorThrown) { 
        console.log('error retrieving data:', errorThrown); 
    })
}

function displayTimes( data, selector ) {
    // example format: "2011-02-12 00:01:31" 
    var timeFormat = d3.time.format("%Y-%m-%d %H:%M:%S");

    // http://stackoverflow.com/a/11526569
    var minimumDate = new Date(8640000000000000);
    var maximumDate = new Date(-8640000000000000); 
    var keys = [];
    for(var key in data) {
        var firstDate = new Date(data[key]["first"]);
        var lastDate = new Date(data[key]["last"]); 
        minimumDate = minimumDate > firstDate ? firstDate : minimumDate; 
        maximumDate = maximumDate < lastDate ? lastDate : maximumDate;
        var days = Math.ceil( Math.abs(lastDate-firstDate)/(1000*60*60*24) )
        keys.push({
            name: key,
            min: firstDate,
            max: lastDate,
            days: days
        });
    }

    keys.sort( function(a,b) {
        return d3.descending(a.min, b.min)
    })

    keys.forEach( function(d) {
        console.log(d.days);
    });

    var ageSet = {};
    keys.forEach( function(d) {
        ageSet[d.days] = true;
    });
    var ages = [];
    for( var d in ageSet ) {
        ages.push(d);
    }
    var ageScale = d3.scale.threshold().domain(ages).range([0,10]);

    var x = d3.time.scale()
        .domain([minimumDate,maximumDate])
        .range([0, 1100]);

    var y = d3.scale.ordinal().domain(
        keys.map( function(d) {
            return d.name;
        })).rangeRoundBands([0,1400]);

    var svg = d3.select(selector).append("g");

    var bar = svg.append("g")
        .selectAll()
        .data(keys, function(d) { return d.name; } )
        .enter().append("g")

    function translate(x,y) {
        return "translate(" + x + "," + y + ")";
    }

    var barColorScale = d3.scale.category10();
    bar.append("rect")
        .attr("width", function(d) { return x(d.max) - x(d.min); })
        .attr("height", y.rangeBand()-4)
        .attr("dy", 2)
        .attr("transform", function(d) { 
            return translate(x(d.min), y(d.name));
        })
        .style("fill", function(d) { return barColorScale(ageScale(d.days)); })
        .style("stroke", "gray")

    bar.append("text")
        .attr("x", 0)
        .attr("y", y.rangeBand() / 2)
        .attr("dy", 10)
        .attr("transform", function(d) { 
            return translate(x(maximumDate), y(d.name));
        })
        .attr("text-anchor", "start")
        .attr("font-size", "25")
        .text(function(d) { return d.name; });
}

function displayModel( data, state, selector ) {
    var svg = d3.select(selector).append("g");
    var nodeGroup = svg.append("g").attr("class","node-group");
    var circleTemplateGroup = svg.append("g").attr("class","circle-template-group");
    var linkGroup = svg.append("g").attr("class","link-group");

    var radius = 300;

    circleTemplateGroup.append("circle")
        .attr("r",301)
        .attr("fill","white")
        .attr("stroke-width", "5")
        .attr("stroke", "#777");

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

    var clusterLayout = d3.layout.cluster()
        .size([360, radius])
        .sort( function(a,b) {
            return d3.ascending(a.degree, b.degree)
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

    var links = [];
    for(var k in data.event_model) {
        for(var k2 in data.event_model[k] ) {
            links.push({
                source:node_names[k],
                target:node_names[k2]
            });
        } 
    }

    var line = d3.svg.line.radial()
        .interpolate("bundle")
        .tension(0.85)
        .radius(function(d) { 
            var jitter = Math.random()/50;
            return d.y-jitter; 
        })
        .angle(function(d) { 
            var jitter = Math.random()/10;
            jitter -= jitter/2;
            return d.x / 180 * Math.PI + jitter; 
        });


    var bundle = d3.layout.bundle();
    var linkColorScale = d3.scale.category10();

    function populationDomain() {
        var result = [];
        for(k in state) {
            result.push(state[k].hits)
        }

        var sorted = result.sort(function(a,b) { 
            if(a<b) return -1;
            if(a>b) return 1;
            return 0
        });

        return [sorted[0], sorted[sorted.length-1]];
    }

    var populationScale = d3.scale.log().domain(populationDomain()).range([1,400]);

    function weightsList() {
        var set = {};
        for(k in data.event_model) {
            for(k2 in data.event_model[k]) {
                var weight = data.event_model[k][k2].weight;
                set[weight] = true;
            }
        }
        var result = [];
        for(k in set) {
            result.push(parseFloat(k));
        }

        return result;
    }

    var linkOpacityScale = d3.scale.linear().domain(weightsList()).range([0.1,0.5]);
    var linkWidthScale = d3.scale.linear().domain(weightsList()).range([1,10]);
    var link = linkGroup.selectAll(".link")
        .data( bundle(links) )
        .enter().append("path")
        .attr("class","link")  
        .style("stroke-linecap","round")
        .style("opacity", function(d) {
            var source_state = d[0].name
            var target_state = d[d.length-1].name
            var weight = data.event_model[source_state][target_state].weight;
            return linkOpacityScale(weight);  
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

    d3.select("input[type=range]").on("change", function() {
        line.tension(this.value / 100);
        link.attr("d", line );
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
        .attr("height",font_size*1.5 )
        .attr("width", function(d) { 
            var population = state[d.name];
            if( population === undefined ) {
                return 1;
            }
            else {
                return populationScale(population.hits);
            }
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
        .style("opacity", "1.0")

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
                .rotate(angle);
            return t();
        })
        .text(function(d) { 
            return d.name + "(" + d.degree + ")"; 
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
