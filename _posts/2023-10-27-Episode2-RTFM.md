# Everything counts in large amounts

![Layer Cake](/img/tflTube/layered-cake.png)

Last time out I walked you through getting information from Tfl API ( transport for london ) and using that to start building a graph in Neo4j.  Before we go much further with this endeavour, it's time to look at how we're approaching the architecture of this code.

I'm going to structure the code in layers rather like a cake,  and who doesn't like Layer Cake or the [film](https://en.wikipedia.org/wiki/Layer_Cake_(film)) of the same name?

![Code cake](/img/tflTube/CodeCake.png)

The top layer of our cake will be the Frontend that a user will interact with.  This could be a web browser based UX , a terminal CLI, a more traditional app or whatever we need. Underneath that will be, what I'm calling, an outcomes layer.  In this case, outcomes are the functionality e.g Find a station, get the shortest route between two stations, update station information, update line informationetc..  that has been exposed to the user in the frontend layer and need to be delivered; there's a lot of business logic here.  To serve the needs of the outcome layer, we'll need data from Tfl and Neo4j graph database and that will be achieved by the next layer which will offer up the data in a series of CRUD interfaces.  Finally, at the bottom, we find a layer who sole purpose is to take care of the requests and responses with Tfl and Neo4j. 






This structure allows us to code ( and test ) each bit seperately.  We can mockup the interfaces so that we can work on a higher layer without needing the ones below it to be completed.  In summary , its flexible.

Where to start though?  Lets pick the bottom (c)[Finbarr Saunders](https://viz.fandom.com/wiki/Finbarr_Saunders)


## But before you come to any conclusions

Recall this snip of code from Episode 1

```python
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

It loops around the list of stations we obtained from the Tfl API and placess them into Neo4j one at a time.  There's approx 272 tube stations so that's the number of individual requests that will be made. 

With a locally installed version of Neo4j e.g Desktop then it's unlikely you noticed how inefficient this is; there's no visible slowness and everything speeds along.  Try this with a remove database where the connection has many hops and latency varies, then it is a different matter.  This is also why you always try and colocate an application with it's database. 


## Tonight I'm in the hands of fate

We don't need to be the passenger with someone else behind the wheel.  We can  improve the situation ourselves by implementing two of the best practices for performance given in the [Neo4j manual](https://neo4j.com/docs/python-manual/current/performance/) for the Python driver. 

- Use query parameters
When the cypher statement is put together, I've concatening values together 
```python
cypher_statement = 'MERGE ( `' + station_id + '`:Station' + \
                    ' { id:' + '"' + station_id + '"' + \
                    ', name:' + '"' + station_name + '"' + \
                    '})'
```
This exposes us to Cypher injections ( bad thing ) and does not allow leveraging of the database query cache.  We can re-write this to use parameters like this

```
 cypher_statement = 'MERGE ( s:Station {id: $station_id, name: $station_name} )'
```

Which has the added bonus of being more readable. 


- Batch data creation

Moving to use batch queries will provide the biggest performance improvement.  Here we define a Cypher statement that also includes all of the information that we want to place into the database in a single request[^1].

Our Cypher statement now changes to this
```
cypher_statement = 'WITH $stations as batch UNWIND batch as station MERGE ( s:Station' {id:station.id, name:station.name})'
```
$stations will be set to hold a Python dictionary at the time when we use .execute_query method from the Neo4j Python Driver. 

The dictionary will look like this  [{ id: '', 'name: ''}] 

To illustrate, look at this example which creates two stations

```

#  Define the dictionary with the two stations 
list_of_stations = [ {"id":"1", "name":"station1"}, {"id":"2", "name":"station2"}]

}
 # Send the Cypher statement
                neo4j_response = neo4jDB_connection.execute_query(cypher_statement, stations=list_of_stations)
```

Fairly straight forward so far.  

There's always a catch and it comes in the data structure that comes back from Tfl API; it does not match what we need.  So some transformation will be required. 

We'll build the list like this

```python
        if tfl_tube_line_stations.json():
            list_of_stations = []
            for station_entry in tfl_tube_line_stations.json():
                # These are the properties to add to our node entry in Neo4j
                # Which we need in the dictionary that will be sent
                # with the Cypher statement

                station_data = { "id":station_entry['id'], "name":station_entry['commonName']  }

                # Add to the list
                list_of_stations.append(station_data)
```

and then shift the code that talks to Neo4j left.


We now have

```python
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
            list_of_stations = []
            for station_entry in tfl_tube_line_stations.json():
                # These are the properties to add to our node entry in Neo4j
                # Which we need in the dictionary that will be sent
                # with the Cypher statement

                station_data = { "id":station_entry['id'], "name":station_entry['commonName']  }

                # Add to the list
                list_of_stations.append(station_data)

            print(list_of_stations)

            # Now ready to send to Neo4j
            # Detail to connect to our Neo4j database
            neo4_uri = '<YOUR NEO4J CONNECTION URL>'
            neo4j_user = '<YOUR NEO4J USERNAME>'
            neo4j_password = '<YOUR NEO4J PASSWORD>'

            # Build the Cypher statement we will use to do a batch creation 
            cypher_statement = 'WITH $stations as batch UNWIND batch as station MERGE ( s:Station {id: station.id, name: station.name})'

            # Connect to Neo4j
            neo4jDB_connection = GraphDatabase.driver(neo4_uri, keep_alive=True, auth=(neo4j_user, neo4j_password))

            # We'll explicitly set the database
            neo4jDB_connection.session(database="Neo4j")
    
            # Send the Cypher statement
            neo4j_response = neo4jDB_connection.execute_query(cypher_statement, stations=list_of_stations)

            # Check the response
            print(neo4j_response.summary.metadata)


```

## Yes, and I'll make it all worthwhile

The completed code with speed up changes is here:- [Episode3](/code/2023-10-27_code.py )


It was a long read this week - thanks for hangin in - and I still have not got to writing the Request & response layer but I've learned something new.  Turns out the manuals are useful !

Until next time, stay safe - bonus for the name of the band whose song lyrics I have used. 


[^1]: If you're inserting a lot of information, then break this into multiple requests or use _neo4j-admin database_ import command


 