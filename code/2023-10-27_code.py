""" MIT License

Copyright (c) 2023 Jonathan Giffard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""


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

            # Now ready to send to Neo4j
            # Detail to connect to our Neo4j database
            neo4_uri = '<YOUR NEO4J CONNECTION URL>'
            neo4j_user = '<YOUR NEO4J USERNAME>'
            neo4j_password = '<YOUR NEO4J PASSWORD>'

            # Build the Cypher statement we will use to create the station entry as a node
            # We're using MERGE rather than CREATE to avoid creating duplicate stations
            # and using a batch
            cypher_statement = 'WITH $stations as batch UNWIND batch as station MERGE ( s:Station {id: station.id, name: station.name})'

            # Connect to Neo4j
            neo4jDB_connection = GraphDatabase.driver(neo4_uri, keep_alive=True, auth=(neo4j_user, neo4j_password))

            # We'll explicitly set the database to 
            neo4jDB_connection.session(database="Neo4j")
    
            # Send the Cypher statement
            neo4j_response = neo4jDB_connection.execute_query(cypher_statement, stations=list_of_stations)

            # Check the response
            print(neo4j_response.summary.metadata)

                

