+++
date = '2024-09-06T00:00:00+01:00'
draft = true
title = 'Query API is now released to all'
+++

The HTTPS based Query API is now GA for Aura and Self-managed customers
For almost 14 years you could query Neo4j via HTTP, originally with a REST API, later via Cypher, with a number of improvements (streaming, type representations etc). Since 2016 the focus has shifted to the binary Bolt protocol, advanced routing and native drivers. The existing HTTP APIs were still running for self-hosted customers but were lacking in features and because of those shortcomings, were not available in the Neo4j Aura Cloud Service. This is about to change now.

The new Query API has been in Beta for our self-managed customers with the April 2024 release of Neo4j 5.19. At the time, we also started it would be coming to Aura in the Summer of 2024. Today we're making good on that promise; Query API is now available on Aura across all tiers and cloud providers for production workloads. We're also pleased to announce that with Neo4j 5.23, self-managed customers can consider the Query API has exited Beta and is now ready for production workloads.

The Query API uses secure HTTP(S) communications to make Cypher requests with a JSON document response. You can also request an extended JSON document that incorporates Type information. As there is no requirement to install and maintain drivers, the Query API will work across a wide range of platforms and in situations where you do not need the rich feature set available in our Drivers or can't install custom libraries or dependencies.

Overall, the Query API is an easily accessible, secure, and efficient method to work with your Neo4j DBs in Aura.

Let's walk through some of the functionality of this new capability for Aura.

---

## Making your first Query API call

You will need an Aura instance to try out the Query API. If you already have one,  along with a set of credentials for it, then skip to 'Query API URL'. If not then sign up for the Aura free tier.

### Create An Aura Instance

- After logging into Aura, select AuraDB, Instances and then New Instance.
- From the various displayed options, choose the smallest instance size, provide a name, and select a region that works best for you.
- Make sure any checkbox is selected and choose Create

- You will be shown the credentials for the new Aura instance. Make sure you download these or record them. You will need these shortly.
_Note: It's really important you do this. You've been warned._

Now is a great time to make a pot of tea as its steeping time is roughly the same as how long it will take for the creation process to complete. [A poster](https://medium.com/r/?url=https%3A%2F%2Fshopandonart.bigcartel.com%2Fproduct%2F50-shades-of-tea-print-pre-order) is available to help you decide on tea strength.

## Query API URL

Communications for the Query API takes place on the standard HTTPS 443 port and uses a URL in the format of  ```https://AURA_HOSTNAME/db/AURA_DATABASE_NAME/query/v2```

- AURA_HOSTNAME is found within the displayed Connection URI of an Aura Instance. In the Aura Console, select AuraDB, Instances and then look in the box for the Aura instance you will use with the Query API for Connection URI, like the one shown here in the red oval box.  The hostname is immediately after neo4j+s://

- AURA_DATABASE_NAME ( for now anyways ) will always be neo4j.

## Authorisation

Authorisation is necessary for every request made to the Query API. Currently, this uses Basic Authentication - a base64 encoded hash of the database username and password. This is set in the header of the request under Authorization. There are plans to introduce the use of JWTs for this purpose later on.

## Your first Query API request

You have everything needed to submit your first Query API request to Aura. Here's a simple example that will check everything is working. Substitute AURA_HOSTNAME and AURA_DB_PASSWORD for your values.

```Bash
curl --location 'https://AURA_HOSTNAME/db/neo4j/query/v2' \
 --user neo4j:AURA_DB_PASSWORD \
 --header 'Content-Type: application/json' \
 --header 'Accept: application/json' \
 --data '{ "statement": "RETURN 1" }'
```

If all is well, you will see a response similar to this

```text
{
 "data": {"fields":["1"],"values":[1]},
 "bookmarks":["FB:kcwQlRkKozmpRoG708y0045J18kJmZA="]
}
```

## A basic Cypher statement

Lets try getting data from the Aura instance using the CURL utility. You will use this Cypher statement to get 5 entries

```TEXT
MATCH (n) RETURN n LIMIT 5
```

With the Query API, the Cypher statement is the value for the statement key. If you want to try this, substitute AURA_HOSTNAME and AURA_DB_PASSWORD for your values.

```Bash
curl --location 'https://AURA_HOSTNAME/db/neo4j/query/v2' \
 --user neo4j:AURA_DB_PASSWORD \
 --header 'Content-Type: application/json' \
 --header 'Accept: application/json' \
 --data '{ "statement": "MATCH (n) RETURN n LIMIT 5" }'
 ```

Here's an example response from the example Movies dataset that has been formatted to improve readability.

```text
{
  "data": {
    "fields": [
      "n"
    ],
    "values": [
      [
        {
          "elementId": "4:751c0ff7-7a1a-448d-9d98-ffc4b4767fef:0",
          "labels": [
            "Person"
          ],
          "properties": {
            "name": "Charlie"
          }
        }
      ],
      [
        {
          "elementId": "4:751c0ff7-7a1a-448d-9d98-ffc4b4767fef:1",
          "labels": [
            "Movie"
          ],
          "properties": {
            "tagline": "Welcome to the Real World",
            "title": "The Matrix",
            "released": 1999
          }
        }
      ],
      [
        {
          "elementId": "4:751c0ff7-7a1a-448d-9d98-ffc4b4767fef:2",
          "labels": [
            "Person"
          ],
          "properties": {
            "name": "Keanu Reeves",
            "born": 1964
          }
        }
      ],
      [
        {
          "elementId": "4:751c0ff7-7a1a-448d-9d98-ffc4b4767fef:3",
          "labels": [
            "Person"
          ],
          "properties": {
            "name": "Carrie-Anne Moss",
            "born": 1967
          }
        }
      ],
      [
        {
          "elementId": "4:751c0ff7-7a1a-448d-9d98-ffc4b4767fef:4",
          "labels": [
            "Person"
          ],
          "properties": {
            "name": "Laurence Fishburne",
            "born": 1961
          }
        }
      ]
    ]
  },
  "bookmarks": [
    "FB:kcwQdRwP93oaRI2dmP/EtHZ/78kAmJA="
  ]
}
```

The Query API only accepts a single Cypher statement in a request. If you have several statements you want to perform in a single request, consider using the Cypher CALL subquery facility or make multiple requests.

---

## Using parameters

Parameterised queries open up many possibilities rather like a fresh hot cup of tea. You can avoid string building and having to escape problematic characters. Additionally, they make caching of execution plans much easier for the Aura DB itself, thus leading to significantly faster query execution times. Consider using parameterised queries as the default pattern when using Cypher in applications and not just with the Query API.

_Note: Definitely use parameterized queries for bulk data loading as they are much quicker than sending one request after another._

A parameterised query is when placeholders (like $name) are used for parameters and the parameter values are supplied at execution time. The Query API supports the use of these with a request body that looks like this

```TEXT
{
'statement': Parameterized Cypher statement that references values,
'parameters': { "key" : [{Values}] }
}
```

Here's an example that loads two entries in a single request

```Bash
curl --location '<https://c22b6d6e.databases.neo4j.io/db/neo4j/query/v2>' \
-- user: neo4j:mypassword \
 --header 'Content-Type: application/json' \
 --header 'Accept: application/json' \
  --data '{ "statement":"UNWIND $items as item MERGE (s:Station {id: item.id}) ON CREATE SET s.name=item.name", "parameters": { "items" : [{"id":"123","name":"station1"},{"id":"456","name":"station2"}]}}'
```

Let us dig into this a bit deeper and see what is going on, starting with the parameters.

```"parameters": { "items" : [{"id":"123","name":"station1"},{"id":"456","name":"station2"}]}```

This is an array of JSON objects with each object having key:value pairs. The array is referenced by its key, items

Onto the Cypher statement itself

```TEXT
UNWIND $items as item
MERGE (s:Station {id: item.id})
ON CREATE SET s.name=item.name
```

We can see the key name from the parameters JSON object array is $items. The array is iterated with use of the Cypher UNWIND command with each entry in the array referenced by item. The values are accessed by using the reference with the wanted property e.g item.name

Read more about using parameters in the [documentation](https://neo4j.com/docs/query-api/current/) for the Query API.

## Other things you can do

There are several other useful things you can do with the Query API in Aura

- You can execute a query under the security context of a different user
- Read your writes, also known as causal consistency
- Profile queries
- Retrieve query counters

More detail about each of these is available in the [Query API documentation.](https://neo4j.com/docs/query-api/current/).

---

## What's next for the Query API?

Since the launch back in April, we've been hard at work on several improvements and we are always interested in your opinions to make the Query API better ( You can supply feedback on the Community Site or in the Drivers area of Discord ) .
Here's what we have on the roadmap at the moment

- Allow for management of transactions to allow for scenarios that require the successful execution of a group of statements where all succeed or none do with rollback support.
- Use secure JWT for auth
- Pagination of results
- General performance improvements

We'll also come back with examples in Python and JS to further illustrate how to use the Query API in applications.
