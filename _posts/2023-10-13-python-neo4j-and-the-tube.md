---
layout: post
title: "Using Python and data from Tfl API"
description: "Building our graph with data from Tfl API using Python"
tags: Neo4j Tfl Python
---

# Episode 1 : Back to school

![London Tube Stations](/img/tflTube/tflStations.png)

To become more familar with the TfL API and working with Neo4j programmatically , I'm going to write some funky Python code to explore and learn more about them. In Agile terms, it's a Spike. The vast majority of this code is likely to be thrown away - no need to make it pretty , optimised or anything like that, just functional.

For the spike, I want to know more about

- How to use the Tfl API to get a list of tube lines
- Create entries in Neo4j using its Python driver

## Install Neo4j locally

I'm going to use Neo4j Desktop for this exercise. It's a local install with a nice UI attached that makes it easy to use and work with.

Download Neo4j Desktop here:- [https://neo4j.com/download/]() and install it.

After the install has completed, launch Desktop and create a new project. Then click on the 'Add' button to , err, add a local DBMS. Give the DBSM a name, a password ( remember this as we will need it shortly ), choose the latest version of Neo4j, then select 'Create' and wait for the process to finish.

Once that's done, go to the project and click on the dbms, then choose 'Start'

You now have a running Neo4j graphdatabase.

## Get the list of tube lines from Tfl

I've already created an account and obtained an API key to access Tfl API. If you haven't , go here [https://api-portal.tfl.gov.uk/]() and then come back.

Lets use some Python code that's going to connect to Tfl API and get the list of Tube lines.

```python
# Use python requests libary for our comms with Tfl
from requests import Request, Session

# Use the json libary for some formatting later
import json

# Use the Neo4j python driver
from neo4j import GraphDatabase


# A session will be used to avoid having to make a new connection with each request we make to Tfl.  Making a new connection takes time.
tfl_session = Session()

# TLR uses an api key for auth
app_key = '<YOUR TFL API KEY>'

# This goes in the request header and we'll set the content type to json
headers = { "Content-Type": "application/json", "app_key": app_key}

# Tfl base URI
base_url = 'https://api.tfl.gov.uk'


# Path the endpoint to get a list of Tube lines
path = "/line/mode/tube/status"

# Put the base and path together
full_url = base_url + path


# Prepare our request
tfl_request = Request('GET', full_url, headers=headers).prepare()


# Send the request to Tfl
tfl_tube_lines = tfl_session.send(tfl_request)

# If we got JSON back
if tfl_tube_lines.json():
    print(json.dumps(tfl_tube_lines.json(), indent=2))
```

Assuming everything works, you will get output like from this from Tfl

```python
[
  {
    "$type": "Tfl.Api.Presentation.Entities.Line, Tfl.Api.Presentation.Entities",
    "id": "bakerloo",
    "name": "Bakerloo",
    "modeName": "tube",
    "disruptions": [],
    "created": "2023-10-10T15:08:36.863Z",
    "modified": "2023-10-10T15:08:36.863Z",
    "lineStatuses": [
      {
        "$type": "Tfl.Api.Presentation.Entities.LineStatus, Tfl.Api.Presentation.Entities",
        "id": 0,
        "statusSeverity": 10,
        "statusSeverityDescription": "Good Service",
        "created": "0001-01-01T00:00:00",
        "validityPeriods": []
      }
    ],
    "routeSections": [],
    "serviceTypes": [
      {
        "$type": "Tfl.Api.Presentation.Entities.LineServiceTypeInfo, Tfl.Api.Presentation.Entities",
        "name": "Regular",
        "uri": "/Line/Route?ids=Bakerloo&serviceTypes=Regular"
      }
    ],
    "crowding": {
      "$type": "Tfl.Api.Presentation.Entities.Crowding, Tfl.Api.Presentation.Entities"
    }
  },
etc..
```

Next step will be to iterate through the list, extract the tube line id and then get use that to get the list of stations

## Obtain the list of stations for a tube line from Tfl

Lets expand the code to go get those stations on a Tube line.

Rather than print the response after the check to see if we got json back, we will iterate our way through each Tube line entry to obtain the Tube line id. This is used with the Tfl endpoint that returns stop points, or stations, for a line. We'll then print the output again to see what we have.

```python
# If we got JSON back
if tfl_tube_lines.json():
    for entry in tfl_tube_lines.json():
        tfl_tube_id = entry['id']

        # Include the line as part of the endpoint that we will use to get the stations
        path = "/line/" + tfl_tube_id + "/stoppoints"

        # Set the full path
        full_url = base_url + path

        # Prepare our request
        tfl_request = Request('GET', full_url, headers=headers).prepare()

        # Send the request to Tfl
        tfl_tube_line_stations = tfl_session.send(tfl_request)

        if tfl_tube_line_stations.json():
            print(json.dumps(tfl_tube_line_stations.json(), indent=2))

```

If all goes ok, and watch for those Python indents, our output will look similar to this

```python
"status": true,
    "id": "940GZZLUHSC",
    "commonName": "Hammersmith (H&C Line) Underground Station",
    "placeType": "StopPoint",
    "additionalProperties": [
      {
        "$type": "Tfl.Api.Presentation.Entities.AdditionalProperties, Tfl.Api.Presentation.Entities",
        "category": "Address",
        "key": "Address",
        "sourceSystemKey": "StaticObjects",
        "value": "Hammersmith (H & C),London Underground Ltd.,Beadon Road,London,W6 7AA"
      },
      {
        "$type": "Tfl.Api.Presentation.Entities.AdditionalProperties, Tfl.Api.Presentation.Entities",
        "category": "Address",
        "key": "PhoneNo",
        "sourceSystemKey": "StaticObjects",
        "value": "0845 330 9880"
      },
    "lat": 51.493535,
    "lon": -0.225013

```

There's a lot of stuff returned from the Tfl endpoint, some of which will be useful - the name, id, and physical location information in the form of lat & lon - and a lot that will not.

If you look at the station list a bit more closely, we find two problems.

The first is a tube line can have several routes - you can see this on the map where the Northen Line splits.

![London Tube Stations](/img/tflTube/tubeMap.png)

Our second is the stations are not in sequence for a route on a line. This will make connecting them together tricky.

We'll solve those next time.

Lets go load this information into Neo4j

## Create nodes in Neo4j with the Python driver

We're going to take each station and create an entry in Neo4j - a node - which will have two properties , the stations id and name.

To make the connection to Neo4j, we'll need the address, user and password. As we're using the local Desktop version, this is straight forward. You can recall the password you created earlier ?

Once we have established the connection we will use Cypher to create the entry. Cypher is the query language used by Neo4j and there's lots of materials to educate yourselve about it. Take one of the free courses at the Neo4j Graph Academy here:- [https://graphacademy.neo4j.com/]() and read the docs here:- [https://neo4j.com/developer/cypher/]()

We'll use MERGE as it will only create an entry if it doesn't already exists. This will avoid duplicates which is handy if there's an error and we need to run the code again.

Change the code starting at the line 'if tfl_tube_line_stations.json():'

As this is Python - think indents !

```python
        if tfl_tube_line_stations.json():
            for station_entry in tfl_tube_line_stations.json():

                # These are the properties to add to our node entry in Neo4j
                station_name = station_entry['commonName']
                station_id = station_entry['id']


                # Detail to connect to our Neo4j database
                neo4_uri = 'bolt://127.0.0.1:7687'
                neo4j_user = 'neo4j'
                neo4j_password = '<YOUR NEO4J PASSWORD>'

                # Build the Cypher statement we will use to create the station entry as a node
                # We're using MERGE rather than CREATE to avoid creating duplicate stations.
                # I've split it across several lines to try and make it easier to read
                cypher_statement = 'MERGE ( `' + station_id + '`:Station' + \
                                   ' { id:' + '"' + station_id + '"' + \
                                   ', name:' + '"' + station_name + '"' + \
                                   '})'

                # Connect to Neo4j
                neo4jDB_connection = GraphDatabase.driver(neo4_uri, keep_alive=True, auth=(neo4j_user, neo4j_password))

                # Send the Cypher statement
                neo4j_response = neo4jDB_connection.execute_query(cypher_statement)

                # Check the response
                print(neo4j_response.summary.metadata)

```

If all goes well you should see entries like this appearing from the code

```
{'query': 'MERGE ( `940GZZLUWWL`:Station { id:"940GZZLUWWL", name:"Walthamstow Central Underground Station"})', 'parameters': {}, 'server': <neo4j.api.ServerInfo object at 0x105786fd0>, 'database': None, 't_first': 1, 'fields': [], 'qid': 0, 'stats': {'contains-updates': True, 'labels-added': 1, 'nodes-created': 1, 'properties-set': 2}, 'type': 'w', 't_last': 0, 'db': 'neo4j'}
{'query': 'MERGE ( `940GZZLUBNK`:Station { id:"940GZZLUBNK", name:"Bank Underground Station"})', 'parameters': {}, 'server': <neo4j.api.ServerInfo object at 0x1057a1e50>, 'database': None, 't_first': 2, 'fields': [], 'qid': 0, 'type': 'w', 't_last': 0, 'db': 'neo4j'}
{'query': 'MERGE ( `940GZZLUWLO`:Station { id:"940GZZLUWLO", name:"Waterloo Underground Station"})', 'parameters': {}, 'server': <neo4j.api.ServerInfo object at 0x1057a9700>, 'database': None, 't_first': 1, 'fields': [], 'qid': 0, 'type': 'w', 't_last': 0, 'db': 'neo4j'}

Process finished with exit code 0
```

Finishing with an exit code of 0 indicates that times are good.

We can now check if we have entries in Neo4j by going over to Neo4j Desktop and choosing the Open button. This will open the Neo4j browser window.

Enter this cyhper statement

```
MATCH (n) RETURN n
```

And you should see a picture like the one at the top of this blog post.

You can downlod the entire code from here:- [Complete Python code](/code/2023-10-13_code.py)

Make sure to change the Tfl API Key to match your own along with password for Neo4j.

## What's next?

Another spike. We need to connect up the stations which means we'll be adding relationships between them. And there's the matter of getting them in the correct sequence on each route on a line.

Then we really need to talk about the code that's been written and how we can structure it better. Some careful munnging together of Python Classes is going be a major factor in that.

Until then, stay safe.
