---
layout: post
title: "Using parameters with Neo4j Query API"
description: ""
tags: Neo4j PM DevEx QueryAPI
---

# Using parameters with the Query API

Imagine that you find yourself needing to perform bulk updates in some shape or form to Neo4j Graph database; it could be a data import, creating relationships between nodes, changing properties or anything else that requires a lot of mutations.

As an example of this, consider the work from an earlier blog post where we represented the London Underground as a graph; Nodes are used for Tube stations and Relationships are the Tube lines that form the network.  

Take the Circle Line. There are 38 tube stations, each of which will be a Node and we will store this information about them

- Name
- London Underground ID
- Long
- Lat
- Tube Zone

To put this into Neo4j we could write a Cypher statement for each station. For example, create a node for Goldhawk Road Tube Station

```TEXT
MERGE ( s:Station {id:, name:"Goldhawk Road Underground Station" , zone:2, lat:51.502005, lon:-0.226715})
```

and then carry on with another 37 Cypher statements for all of the remaining tube stations on the Circle line.

Sending a single Cypher statement in this way is not very efficient. Apart from the overhead of establishing network connection each and every time, it skips over an optimisation that's available with Neo4j - Parameterized Queries


## Parameterized queries

A parameterized query is a query in which placeholders are used for parameters and the parameter values are supplied at execution time. This means you don't need to resort to using multiple statements mentioned previously.  It also means that you can avoid string building to create a query and having to escape problematic characters. Additionally, parameters make caching of execution plans much easier for Cypher, thus leading to significantly faster query execution times.

Parameterized queries are available for direct use with Cypher , Neo4j drivers and the Query API.

The Query API supports the use of parameters ( link to docs page ) with a request body that looks like this

```JSON
{
'statement': Parameterized Cypher statement that references values,
'parameters': { "key" : [{Values}] }
}
```

If we used Query API with parameters for the Circle Line , then we could do this in a single request ( I'll just put 5 Circle Line stations in to keep it readable ).

```JSON
{
'statement':'WITH $items as batch UNWIND batch as item MERGE ( s:Station {id: item.id, name: item.name, zone: item.zone, lat:item.lat, lon:item.lon }),
'parameters': { "items" : [
    {'id': '940GZZLUHSC', 'name': 'Hammersmith (H&C Line) Underground Station', 'zone': '2', 'lat': 51.49339, 'lon': -0.225033},
    {'id': '940GZZLUGHK', 'name': 'Goldhawk Road Underground Station', 'zone': '2', 'lat': 51.502005, 'lon': -0.226715},
    {'id': '940GZZLUSBM', 'name': "Shepherd's Bush Market Underground Station", 'zone': '2', 'lat': 51.505579, 'lon': -0.226375},
    {'id': '940GZZLUWLA', 'name': 'Wood Lane Underground Station', 'zone': '2', 'lat': 51.509669, 'lon': -0.22453}, 
    {'id': '940GZZLULRD', 'name': 'Latimer Road Underground Station', 'zone': '2', 'lat': 51.513389, 'lon': -0.217799}
    ]
  }
}
```

Lets dig into this a bit deeper and see what is going on

We'll start with parameters.  

```JSON
'parameters': { "items" : [
    {'id': '940GZZLUHSC', 'name': 'Hammersmith (H&C Line) Underground Station', 'zone': '2', 'lat': 51.49339, 'lon': -0.225033},
    {'id': '940GZZLUGHK', 'name': 'Goldhawk Road Underground Station', 'zone': '2', 'lat': 51.502005, 'lon': -0.226715},
    {'id': '940GZZLUSBM', 'name': "Shepherd's Bush Market Underground Station", 'zone': '2', 'lat': 51.505579, 'lon': -0.226375},
    {'id': '940GZZLUWLA', 'name': 'Wood Lane Underground Station', 'zone': '2', 'lat': 51.509669, 'lon': -0.22453}, 
    {'id': '940GZZLULRD', 'name': 'Latimer Road Underground Station', 'zone': '2', 'lat': 51.513389, 'lon': -0.217799}
    ]
  }
```

This is an array of JSON objects, each object having key:value pairs. The array is referenced by its key, items

Onto the Cyper statement.  We can see the key name being used - items - and the array is going to be referenced by the label batch

```TEXT
WITH $items as batch
```

Next step is to loop around each JSON object in the array like so

```TEXT
UNWIND batch as item
```
 
Then we get to the Cypher statement that creates a new node if it does not already exist.  We obtain the values we want to use by refering to the key name e.g item.name

```TEXT
MERGE ( s:Station {id: item.id, name: item.name, zone: item.zone, lat:item.lat, lon:item.lon })
```

## What difference does it make?

To illustrate the difference parameters make, we'll run a comparative test that creates the entire London Tube Network in Neo4j.  We'll use Neo4j Desktop as Query APi is not ( yet ) available in Aura.  For the code, we can modify that used in previous articles on this topic.

As for timing, we'll use a Python decorator to see how long the Neo4j request function call takes.  Here it is

```PYTHON
def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        return value
    return wrapper_timer
```

As we want to focus on Neo4j, lets re-use network connection to avoid the overhead of establishing one for each request.  We will be using Neo4j Desktop locally so network conditions should not be an issue.  

Another variable outside of our control is the response of the TFL API.  As we're not measuring that, we can ignore it.

Each test, with Parameters and then without Parameters, was run 3 times using these steps each time
Once you have everything ready
- Start Neo4j
- Run Python code
- Note timing
- Empty Neo4j database with MATCH(n) DETACH DELETE(n)
- Stop Neo4j

The resulsts are as follows.  All timings are in seconds

| Test run | With Parameters    | Without Parameters |
| -------- | ------- | ------- |
| 1  | 2.5783 | 15.1745 |
| 2 | 3.0867  | 15.5487|
| 3    | 2.6416 | 16.8796 |
|    |  |   |
|    |  |   |
| **Average**   | 2.6416 |  15.5487 |

It's hard to avoid the conclusion - use parameters, they save a lot of time

## Try it out at home
If you want to follow along at home then you will need
- [Neo4j Desktop ](https://neo4j.com/download/)
- Using Neo4j Desktop, create a new database that uses Neo4j 5.19
- Change the database configuraiton to add this line 
```server.http_enabled_modules=TRANSACTIONAL_ENDPOINTS,UNMANAGED_EXTENSIONS,BROWSER,ENTERPRISE_MANAGEMENT_ENDPOINTS,QUERY_API_ENDPOINTS```
- Python 3.12 or newer
- [TFL API key](https://api.tfl.gov.uk)
- The two Python files,  [With parameters ](/code/2024-04-26-withParameters_code.py) and [Without parameters ](/code/2024-04-26-withoutParameters_code.py)
- Modified the Python files to use your Neo4j username , password and your TLF API key











Laters

JG
