---
layout: post
title: "Explicit transactions with the Neo4j Query API coming shortly "
description: "Introducing explicit transactions"
tags: Neo4j PM DevEx QueryAPI  Aura
---

# Explicit transactions with Neo4j Query API

Over the last few months, we've been working hard (well, the engineers have — I've just been sipping tea and eating biscuits) to add support for Explicit Transactions to the Query API. I'm excited to announce that this feature will be available real soon for our self-managed and Aura customers.

Up to now you gave the Query API a Cypher statement and it managed transaction  for you -  an Implicit Transaction.  Explicit Transactions hands over control of the transaction , from start to finish, to you.

This allows you to group related queries together, treating them as a single logical operation. For example, adding a new movie along with its actors and directors can be managed as one cohesive operation.  Since Neo4j is ACID-compliant, all queries within a transaction are executed as a unit: they either all succeed or none do. This ensures consistency and prevents partial updates.

The Query API uses the same workflow as for any other transaction with Neo4j

- Begin a transaction.
- Perform database operations.
- Commit or roll back the transaction.

It's important to note that transactions don't last indefinitely. Once created, a transaction has a 30-second time limit before it expires.

___

The Query API has these new paths for explicit transactions

| Path | Purpose |
| -------- | ------- |
| /tx | A POST operation to this path will return a tx id in the response. |
| /tx/{transaction id} | A POST operation to this path with a transacton id is used for database operations. |
| /tx/{transaction id}/commit | A POST operation to this path with a transacton id is used to commit database operations. |
| /tx/{transaction id} | A DELETE option to this path  will rollback all database operations for the given transaction id |

___

## Explicit transaction workflow

The first step is to perform a POST operation to /tx .  This will return a transaction ID

With the transaction ID appended to the /tx path,  /tx/{transaction ID}, we can perform a series of POST requests that contain Cpyher statements such that our logical operation is completed.  For example adding a movie , it's Actors and Director.

To commit the transaction, we make a POST request to  /tx/{transaction ID}/commit.  Or to rollback , we would use a DELETE request to  /tx/{transaction ID}

__Note__: All operations must be made to the same Neo4j DB Server.  If you have a clustered environment, you must implement a mechanism to do this.  For example, HAProxy has [sticky sessions](https://www.haproxy.com/blog/enable-sticky-sessions-in-haproxy) and other API Gateways have similar approaches to meet this requirement.

#### Explicit Transaction with Aura

Explicit transactions with Aura follow the workflow that has just been described but there's an important difference; at the begining of a transaction, when a POST request is made is to /tx, Aura returns a key:value pair in the header __and__ the transaction id.

Aura then requires you to include the key:value pair in each request that you make for that transaction. This ensures   ensures correct routing within the Aura cloud infrastructure.

Here's a Python example to illustrate this with inline comments to explain what's going on at each stage.

__Note:__ This is structured to help show how this feature works.  It's really not a best practice example of how to do this!

__.env file__  Create a .env file in the same folder as this Python script will run.  The .env file should have the following content. Change the values to match your own Aura setup.

```Text
NEO4J_URI=neo4j+s://FQDN_TO_AURA_INSTANCE
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=AURA_INSTANCE_PASSWORD
```

```Python
import requests
from requests.auth import HTTPBasicAuth
import os

from dotenv import load_dotenv

class MyConfiguration():
    """
    Reads configuration from .env file in the same folder as this Python file
    """
    load_dotenv()
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    AURA_INSTANCEID = os.getenv('AURA_INSTANCEID')
    AURA_INSTANCENAME = os.getenv('AURA_INSTANCENAME')



def AuraExpliciTX(MyConfig):
    # Set the URL to use for the Query API with explicit transaction
    query_uri = f"https://{MyConfig.NEO4J_URI.split('//')[1]}/db/neo4j/query/v2"

    # Set the auth to for username & password
    query_auth = HTTPBasicAuth(MyConfig.NEO4J_USERNAME, MyConfig.NEO4J_PASSWORD)

    # Headers for our requests
    query_headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # Begin our transaction
    response = requests.post(f"{query_uri}/tx", headers=query_headers, auth=query_auth)

    # Extract the transaction id.  This will be added to the end of the URI
    # to associate database operations with the transaction
    tx_id = response.json()['transaction']['id']

    # Add the affinity to the request header.  This ensures the requests for the transaction
    # are routed correctly in Aura
    query_headers['neo4j-cluster-affinity'] = response.headers['neo4j-cluster-affinity']

    # In our transaction context, create a movie
    query_cypher = { 'statement': 'CREATE (OfficeSpace:Movie {title:"Office Space", released:1999, tagline:"Works sucks?"})'}
    response = requests.post(f"{query_uri}/tx/{tx_id}", headers=query_headers, auth=query_auth, json=query_cypher)


    # In our transaction context, now add actors
    query_cypher = {
        'statement': 'WITH $items as batch UNWIND batch as item CREATE (:Person {name:item.name, born:item.born})',
        'parameters': {"items": [ {'id': 'Aniston', 'name': 'Jennifer Aniston', 'born': 1969},
                                  {'id': 'Livingston', 'name': 'Ronald Livingston', 'born': 1967},
                                  {'id': 'Cole', 'name': 'Gary Cole', 'born': 1956},
                                  {'id': 'Root', 'name': 'Stephen Root', 'born': 1951}]}
    }
    response = requests.post(f"{query_uri}/tx/{tx_id}", headers=query_headers, auth=query_auth, json=query_cypher)

    # In our transaction context, associate our actors to the Movie
    query_cypher = {
        'statement': 'WITH $items as batch UNWIND batch as item CREATE (p:Person {name: item.name} )-[:ACTED_IN { roles: item.roles }]-> (m:Movie { title:"Office Space"})',
        'parameters': {"items": [
            { 'name': 'Jennifer Aniston', 'roles': ['Joanne']},
            {'name': 'Ronald Livingston', 'roles': ['Peter ']},
            {'name': 'Gary Cole', 'roles': ['Lumbergh'], },
            {'name': 'Stephen Root', 'roles': ['Milton']}
        ]}
    }
    response = requests.post(f"{query_uri}/tx/{tx_id}", headers=query_headers, auth=query_auth, json=query_cypher)

    # list all of the actors in Office Space
    # This will only work within the context of the transaction
    query_cypher = {'statement': 'MATCH (p:Person)-[:ACTED_IN]->(m:Movie) RETURN m.title as title, COLLECT( p.name)'}
    response = requests.post(f"{query_uri}/tx/{tx_id}", headers=query_headers, auth=query_auth, json=query_cypher)
    print(f"List of actors inside of TX context: {response.json()['data']['values']}")

    # Try to list all of the actors in Office Space outside of the transaction context
    # This will return an empty set as the database operations have not yet been committed
    query_cypher = {'statement': 'MATCH (p:Person)-[:ACTED_IN]->(m:Movie) RETURN m.title as title, COLLECT( p.name)'}
    response = requests.post(query_uri, headers=query_headers, auth=query_auth, json=query_cypher)
    print(f"List of actors outside of TX context: {response.json()['data']['values']}")

    # Commit the transaction
    response = requests.post(f"{query_uri}/tx/{tx_id}/commit", headers=query_headers, auth=query_auth)

    # Check if transaction was committed ok
    if response.status_code == 202:
        print(f"Committed transaction {tx_id}")
        
        # The resulf of our database operations are now available to all
        # We can now list all of the actors in Office Space outside of the TX context
        query_cypher = { 'statement': 'MATCH (p:Person)-[:ACTED_IN]->(m:Movie) RETURN m.title as title, COLLECT( p.name)'}
        response = requests.post(query_uri, headers=query_headers, auth=query_auth, json=query_cypher)
        print(f"List of actors outside of TX context: {response.json()['data']['values']}")

    else:
        print(f"Transaction with id of {tx_id} was not committed\nThe transaction has timed out or an error occurred triggering a rollback")


if __name__ == '__main__':
    AuraExpliciTX(MyConfiguration)


```
