---
layout: post
title: "My reference python code for Neo4j"
description: "Basic connection to Neo4j with Python"
tags: Neo4j PM DevEx Python
---

## When you can't connect

Dear Reader,

I find when having those 'why can't i connect to Neo4j' moments, having a reference code that you know works is rather useful.

Here's my reference Python code for that situatin in case anyone finds it useful

There are two files, requirements.txt and the Python code, neo4jTest.py. These are given below. Save them both in the same folder.

The requirements file which will install the latest version of the Neo4j Python driver. Save as requirements.txt

```Text
neo4j

```

The Python file. Save this as neo4jTest.py

```Python
# Use the Neo4j python driver
from neo4j import GraphDatabase

# The cypher statement
cypher_statement = 'MATCH (n) RETURN n LIMIT 1'

# Detail to connect to our Neo4j server running locally
# If this was a cluster or Aura, use neo4j:// or neo4j+s://
# Make sure this matches your connection requirement
neo4_uri = 'bolt://localhost:7687'
neo4j_user = 'neo4j'
neo4j_password = 'password'

# Connect to Neo4j
neo4jDB_connection = GraphDatabase.driver(neo4_uri, keep_alive=True, auth=(neo4j_user, neo4j_password))

# Send the Cypher statement
neo4j_response = neo4jDB_connection.execute_query(cypher_statement)

# Check the response
print(neo4j_response.records)
```

At the command line, do this in the folder you saved those two files in.

```Console
pip install -r ./requirements.txt.
python neo4jTest.py
```
