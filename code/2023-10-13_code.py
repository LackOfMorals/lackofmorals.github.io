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
            for station_entry in tfl_tube_line_stations.json():
                # These are the properties to add to our node entry in Neo4j
                station_name = station_entry['commonName']
                station_id = station_entry['id']

                # Detail to connect to our Neo4j database
                neo4_uri = 'bolt://127.0.0.1:7687'
                neo4j_user = 'neo4j'
                neo4j_password = '<YOUR NEO4J DB PASSWORD>'

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



