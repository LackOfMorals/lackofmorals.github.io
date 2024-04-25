""" MIT License

Copyright (c) 2024 Jonathan Giffard

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
from requests.exceptions import HTTPError,ReadTimeout,ConnectionError,RequestException
from requests.auth import HTTPBasicAuth

# Use the json libary for some formatting later
import json

# Use the Neo4j python driver
from neo4j import GraphDatabase

# Exceptions we want to deal with
from neo4j.exceptions import DriverError, Neo4jError


# Used in our time decorator that returns how long a function ran for
import functools
import time

def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        return value, elapsed_time
    return wrapper_timer

class MakeRequests:
    """
        Handles http requests - GET , PUT, POST, DELETE
        for the Aura API endpoints

        Assumes that the caller then deals with whatever
        the response holds
    """

    def __init__(self):
        # We will re-use http sessions to avoid the
        # overhead of creating new sessions for each request
        self.network_session = Session()

    def  make_request(self, request_to_send):
        """
           Makes a request to a network endpoint and expects the response as a JSON document
           :param request_to_send A request object

           :return: The JSON Response back from endpoint
           """
        try:
            # Send the request
            request_response = self.network_session.send(request_to_send)
            request_response.raise_for_status()

        except HTTPError as errh:
            print("HTTP Error")
            print(errh.args[0])
            print(f"Request body {request_to_send.body}")
            exit(0)
        except ReadTimeout as errrt:
            print("Time out")
            print(errrt)
        except ConnectionError as conerr:
            print("Connection error")
            print(conerr)
        except RequestException as errex:
            print("Exception request")
            print(errex)

        return request_response.json()



class Neo4jRequests(MakeRequests):
    def __init__(self):
        # Call init for inherited classes
        super().__init__()

    @timer
    def request(self, cypher_statement, cypher_parameters=None):
        """
            Executes a cypher statement to a neo4j server

            :param cypher_statement mandatory cypher_statement a string containing the cypher to execute
            :param parameter_list optional a list of dictionaries that contain properties to use with a CREATE or MERGE cypher statement
            :return: JSON response from neo4j
            """

        # Connection information
        neo4_uri = 'http://127.0.0.1:7474/db/neo4j/query/v2'
        neo4j_user = '<YOUR NEO4J USERNAME>'
        neo4j_password = '<YOUR NEO4J PASSWORD>'

        # This goes in the request header and we'll set the content type to json
        headers = {
            "Content-Type": "application/json"
        }

        # The body of the Neo4j request
        if cypher_parameters is not None:
            request_body = {
                "statement": cypher_statement,
                "parameters": cypher_parameters
            }
        else:
            request_body = {
                "statement": cypher_statement
            }

        # Prepare our request
        neo4j_request = Request(
            'POST',
            neo4_uri,
            headers=headers,
            json=request_body,
            auth=HTTPBasicAuth(neo4j_user, neo4j_password)
        ).prepare()

        # Make the request
        neo4j_json_response = self.make_request(neo4j_request)

        return neo4j_json_response

class tflRequests(MakeRequests):
    def __init__(self):
        # Call init for inherited classes
        super().__init__()

    def request(self,endpoint_path):
        """
        Makes a request to transport for London API
        Will only ever do GET
        :param endpoint_path The path to the endpoint to make a request to

        :return: Response back from tfl in JSON form
        """
        make_requests = MakeRequests()

        # TLR uses an api key for auth
        app_key = '<YOUR TFL API KEY>'

        # This goes in the request header and we'll set the content type to json
        headers = {"Content-Type": "application/json", "app_key": app_key}

        # Tfl base URI
        base_url = 'https://api.tfl.gov.uk'

        # Put the base and path together
        full_url = base_url + endpoint_path

        # Prepare our request
        tfl_request = Request('GET', full_url, headers=headers).prepare()

        # Make the request
        tfl_json_response = make_requests.make_request(tfl_request)

        return tfl_json_response

def main():
    # This will store the total time , in seconds, that
    # is spent in neo4j requests
    total_neo4j_time = 0

    # The object for making requests to Neo4j that uses sessions
    neo4j_request = Neo4jRequests()

    # The object for making requests to TFL that uses sessions
    tfl_requests = tflRequests()

    # Path the endpoint to get a list of Tube lines
    tfl_tube_lines = tfl_requests.request("/line/mode/tube/status")

    for entry in tfl_tube_lines:
        tfl_tube_id = entry['id']

        # We will use a single tfl endpoint to get stations
        # and station order on a line

        print(f"Processing tube line {tfl_tube_id}")
        stations_and_routes = tfl_requests.request("/Line/" + tfl_tube_id + "/Route/Sequence/outbound")

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
                cypher_statement = 'WITH $items as batch UNWIND batch as item MERGE ( s:Station {id: item.id, name: item.name, zone: item.zone, lat:item.lat, lon:item.lon, location:point({latitude:toFloat(item.lat), longitude:toFLoat(item.lon)}) })'
                cypher_parameters = {"items": list_of_stations}

                # Make the request to Neo4j
                neo4j_response_body, elapsed_time = neo4j_request.request(cypher_statement, cypher_parameters)

                # Add time taken to our running total
                total_neo4j_time = total_neo4j_time + elapsed_time

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

                cypher_parameters = {"items": station_route_sequence}
                cypher_statement = f"WITH $items as batch UNWIND batch as item MATCH ( s1:Station {{ id:item.id }} ) " \
                                   f"MATCH ( s2:Station {{ id:item.id_next }}) " \
                                   f"MERGE (s1 ) - [r1:ROUTE {{ name:'{tube_line}' }}] -> (s2) - [r2:ROUTE {{ name:'{tube_line}' }}] -> (s1)"

                # Make the request to Neo4j
                neo4j_response_body, elapsed_time = neo4j_request.request(cypher_statement, cypher_parameters)

                # Add time taken to our running total
                total_neo4j_time = total_neo4j_time + elapsed_time

            print(f"Finsihed processing {tfl_tube_id}")

    print('Done')
    print(f"Elapsed time: {total_neo4j_time:0.4f} seconds")
    print("Deleting nodes...")
    neo4j_request.request("MATCH(n) DETACH DELETE(n)")

    return


if __name__ == "__main__":
    main()



