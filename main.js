"use strict";

$( document ).ready( main );

function main() {
    $.getJSON("results.json", function(d) {
        displayData( processData(d) );
    }); 
}

function displayData( graphData ) {
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
        var appearance = {};
        if( p < 0.01 ) {
            appearance = { style: 'stroke-width: 1px;' };
        }
        else if( p < 0.10 ) {
            appearance = { style: 'stroke-width: 5px;' };
        }
        else if( p < 0.40 ) {
            appearance = { style: 'stroke-width: 30px;' };
        }
        else {
            appearance = { style: 'stroke-width: 60px;' };
        }
        g.addEdge( null, a,b, appearance )
    });

    var renderer = new dagreD3.Renderer();
    renderer.run(g, d3.select("svg g"));
    console.log("done.");
}

function processData( theData ) {
    var nodeList = [];
    var linkList = [];

    function findNodes( dict ) {
        for( var key in dict ) {
            var index = nodeList.indexOf( key );
            if( index < 0 ) {
                nodeList.push( key );
            }
        }
    }

    // Build an array of nodes
    findNodes( theData );

    function findLinks( dict ) {
        for( var key in dict ) {
            var connectedDict = dict[key];
            var sourceIndex = nodeList.indexOf( key );
            for( var connectedKey in connectedDict ) {
                var probability = connectedDict[connectedKey].toFixed(2);
                var targetIndex = nodeList.indexOf( connectedKey );
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

    findLinks( theData );

    nodeList = nodeList.map( function(item, index) {
        return {
            name: item,
            group: index,
            size: 6,
        }
    });

    var result = {
        nodes: nodeList,
        links: linkList,
    }

    return result;
}
