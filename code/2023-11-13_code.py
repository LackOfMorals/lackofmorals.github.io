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

# Exceptions we want to deal with
from neo4j.exceptions import DriverError, Neo4jError

def neo4j_request(cypher_statement, parameter_list=[]):
    """
    Executes a cypher statement to a neo4j server

    :param cypher_statement mandatory cypher_statement a string containing the cypher to execute
    :param parameter_list optional a list of dictionaries that contain properties to use with a CREATE or MERGE cypher statement
    :return: JSON response from neo4j
    """

    # execute the cypher statement
    neo4_uri = '<YOUR_NEO4J_SERVER_URI>'
    neo4j_user = '<YOUR_NEO$J_USER>'
    neo4j_password = '<YOUR_NEO4J_PASSWORD>'

    neo4jdb_driver = GraphDatabase.driver(neo4_uri, keep_alive=True, auth=(neo4j_user, neo4j_password))

    # Explicity set the Neo4j database to use with the Cypher statement to Neo4j
    neo4jdb_driver.session(database="Neo4j")

    # using try / except allows us to start dealing with errors that can occur
    try:
        # Check if we have parameters to send with the Cypher and include them if we do
        if len(parameter_list) > 0:
            neo4j_response = neo4jdb_driver.execute_query(cypher_statement, items=parameter_list)
        else:
            neo4j_response = neo4jdb_driver.execute_query(cypher_statement)

    except [DriverError, Neo4jError] as exception:
        print("%s raised an error: \n%s", cypher_statement, exception)
        raise

    # Close the driver when it's no longer required
    neo4jdb_driver.close()

    return neo4j_response

def tfl_request(endpoint_path):
    """
    Makes a request to transport for London API
    Will only ever do GET
    :param endpoint_path The path to the endpoint to make a request to

    :return: Response back from tfl in JSON form
    """

    # TLR uses an api key for auth
    app_key = '<YOUR_TFL_API_KEY>'

    # This goes in the request header and we'll set the content type to json
    headers = {"Content-Type": "application/json", "app_key": app_key}

    # Tfl base URI
    base_url = 'https://api.tfl.gov.uk'

    # Put the base and path together
    full_url = base_url + endpoint_path

    # A session will be used to avoid having to make a new connection with each request we make to Tfl.  Making a new connection takes time.
    tfl_session = Session()

    # Prepare our request
    tfl_request = Request('GET', full_url, headers=headers).prepare()

    try:
        # Send the request to Tfl
        tfl_response = tfl_session.send(tfl_request)

    except Exception as e:
        print("%s raised an error: \n%s", tfl_request, e)
        raise

    return tfl_response.json()

def main():

    # Path the endpoint to get a list of Tube lines
    tfl_tube_lines = tfl_request("/line/mode/tube/status")

    for entry in tfl_tube_lines:
        tfl_tube_id = entry['id']

        # We will use a single tfl endpoint to get stations
        # and station order on a line

        print(f"Processing tube line {tfl_tube_id}")
        stations_and_routes = tfl_request("/Line/" + tfl_tube_id + "/Route/Sequence/outbound")

        #If we got back JSON with stations in , then we're good to go
        if "stations" in stations_and_routes:
            # Our station information is held in stopPointSequences list
            # That has one or more dictionaries that contain the information we need
            # Lets loop around stopPointSequences and then the stations in each stopPoint
            list_of_stations = []
            for stop_point_entry in stations_and_routes['stopPointSequences']:
                for station_entry in stop_point_entry['stopPoint']:
                    # These are the properties to add to our node entry in Neo4j
                    # Which we need in the dictionary that will be sent
                    # with the Cypher statement
                    station_data = None

                    # We don't need information about Transport interchanges
                    # So we'll ignore them
                    if station_entry['stopType'] != 'TransportInterchange':
                        station_data = {'id': station_entry['id'],
                                        'name': station_entry['name'],
                                        'zone': station_entry['zone'],
                                        'lat': station_entry['lat'],
                                        'lon': station_entry['lon']
                                        }
                        # Add to our list of stations that we will
                        # put into our graph database
                        list_of_stations.append(station_data)

                # We have the complete list of stations for this stopPoint
                # build the Cypher statement
                # We're using MERGE rather than CREATE to avoid creating duplicate stations
                # and using a batch - which is quicker
                cypher_statement = 'WITH $items as batch UNWIND batch as item MERGE ( s:Station {id: item.id, name: item.name, zone: item.zone, lat:item.lat, lon:item.lon})'

                # Make the request to Neo4j
                neo4j_request(cypher_statement, list_of_stations)

            # Now we have added the stations, we can now start to wire them together
            # We create an ordered list of stations
            sequenced_station_ids = []

            for route in stations_and_routes['orderedLineRoutes']:
                # The route is stored in naptanIds list
                # and there can be more than one route per tube line
                station_route_count = len(route['naptanIds'])
                print(f"There are {station_route_count} stations on this route")
                station_route_sequence = []
                for station_id in route['naptanIds']:
                    station_id_index = route['naptanIds'].index(station_id)
                    if station_id_index + 1 != station_route_count:
                        station_join = {
                            'id': station_id,
                            'id_next': route["naptanIds"][station_id_index + 1]
                        }

                    station_route_sequence.append(station_join)

                # Build Cypher statement to join up the stations on this route

                # Force tube_line to be uppercase as this matches best practice for relationships in Neo4j
                # and replace any - with a _ or we'll get a Cypher error
                tube_line = tfl_tube_id.upper().replace("-", "_")

                cypher_parameters = station_route_sequence
                cypher_statement = f"WITH $items as batch UNWIND batch as item MATCH ( s1:Station {{ id:item.id }} ) " \
                                   f"MATCH ( s2:Station {{ id:item.id_next }}) " \
                                   f"MERGE (s1 ) - [r1:{tube_line} {{ name:'{tube_line}' }}] -> (s2) - [r2:{tube_line} {{ name:'{tube_line}' }}] -> (s1)"

                print(f"Station sequence {cypher_parameters}")

                neo4j_request(cypher_statement, cypher_parameters)

                print(f"Finsihed processing {tfl_tube_id}")

    print('Done')

    return


if __name__ == "__main__":
    main()



