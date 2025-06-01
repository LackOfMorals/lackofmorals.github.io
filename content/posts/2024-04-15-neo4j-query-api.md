+++
date = '2024-04-15T00:00:00+01:00'
draft = true
title = 'An introduction to the new Query API in Neo4j 5.19'
+++

I've been lucky enough to work with our Neo4j Engineers to create a new API for Neo4j that allows the execution of Cypher statements in the form of network requests without requiring a driver to be installed. There was thought given ( briefly ) to asking the Internet for a what to call this but that doesn't [always turn out well](https://en.wikipedia.org/wiki/Boaty_McBoatface#Naming). In the end we went with the simple approach of naming it after what it does and called it the **Query API**. It's available now with Neo4j 5.19 and will be coming to Aura , our cloud service, in early Summer this year.  For those of you who are using the existing HTTP API, it's not retiring anytime soon and will be kept updated with fixes for critical defects and security vulnerabilities.  You'll be able to choose which one to use.

## Say hello to the new Query API
Since the early days of Neo4j it has been possible to use the [HTTP API](https://neo4j.com/docs/http-api/current/) , to send Cypher and get back the results without requiring installation of a driver.  The current HTTP API has proven popular and provide several benefits for our Developer community:-

- It's convenient for experimenting, works on platforms where a Driver might not be available
- Avoids having to install and maintain Drivers
- Works well where the rich feature set offered by Drivers is not required.

 Although the HTTP API has withstood the passage of time rather well, it is not entirely immune to ageing.   After much consideration, it was decided to invest in building a new API that retained the benefits of the HTTP API, designed with modern architectural patterns and technology, be consistent in its usage, and work with Aura, something the HTTP API does not do. I'm forever greatful to the Engineers who made that feature list a reality
 
Lets start to explore the approach taken by the Query API with an example, based on our Movies sample dataset.


## First steps with the Query API

To try out the Query API you will need the following.

- Neo4j 5.19 running locally ( community or Enterprise ). Using [Neo4j Desktop](https://neo4j.com/download/) or a [Docker container](https://neo4j.com/docs/operations-manual/current/docker/) will be easiest way to do this
- The username is neo4j with the password set to password
- The database with the Movies Graph Database dataset is called neo4j
- You have curl installed and are somewhat familiar with it

The Query API is off by default so we will need to turn it on.  Shtudown Neo4j and use your favourite text editor to open the neo4j.conf file.  WHen you have the neo4j.conf file open, search for this line

```TEXT
server.http.enabled=true
```
Immediately after this line , add the line to enable the Query API.

- If you are using Neo4j community , add  

```TEXT
server.http_enabled_modules=TRANSACTIONAL_ENDPOINTS,UNMANAGED_EXTENSIONS,BROWSER,QUERY_API_ENDPOINTS
```

- If you are using Neo4j Enterprise, add

```TEXT
server.http_enabled_modules=TRANSACTIONAL_ENDPOINTS,UNMANAGED_EXTENSIONS,BROWSER,ENTERPRISE_MANAGEMENT_ENDPOINTS,QUERY_API_ENDPOINTS
```

Save the file and startup Neo4j.  Once Neo4j is back running, go to the command prompt. Copy & paste the following then press enter

```BASH
curl - location 'http://127.0.0.1:7474/db/neo4j/query/v2' \
 - header 'Content-Type: application/json' \
 - header 'Accept: application/json' \
 - header 'Authorization: Basic bmVvNGo6cGFzc3dvcmQ=' \
 - data '{
"statement": "MATCH (nineties:Movie) WHERE nineties.released >= 1990 AND nineties.released < 2000 RETURN nineties.title "
}'
```

We've just use the Query API to ask Neo4j for all of the movies that were released between 1990 and 2000.  If all is working as we expect, you should see this.

```text
{"data":{"fields":["nineties.title"],"values":["The Matrix","The Devil's Advocate","A Few Good Men","As Good as It Gets","What Dreams May Come","Snow Falling on Cedars","You've Got Mail","Sleepless in Seattle","Joe Versus the Volcano","When Harry Met Sally","That Thing You Do","The Birdcage","Unforgiven","Johnny Mnemonic","The Green Mile","Hoffa","Apollo 13","Twister","Bicentennial Man","A League of Their Own"]},"bookmarks":["FB:kcwQQdg6mV80SxC+JcAk3s1YyRWQ"]}%
```

If you didn't get this, check that you have everything setup as described earlier and you have made the changes to the neo4j.conf file. 

## Digging into the request we just made

All of the requests to the Query API require authorization. This needs the header key, Authorization , to have a value of 

```Basic ( Base64 encoded <Neo4j username>:<Neo4j password> )```

You can see this in the curl command we used used here:-

```TEXT
- header 'Authorization: Basic bmVvNGo6cGFzc3dvcmQ='
```
There's many ways to base 64 encode  ```<Neo4j username>:<Neo4j password> ``` .  If you want to quickly try this, there's a website , <https://www.base64encode.org>, that will do this for you.

With our setup - username of neo4j and a password of password -  we enter neo4j:password into the Encode box , select *Encode* and the base 64 encoded is then diplayed -   bmVvNGo6cGFzc3dvcmQ=

The other part of the curl statement that is of interest is where have the Cypher request

```
- data '{
"statement": "MATCH (nineties:Movie) WHERE nineties.released >= 1990 AND nineties.released < 2000 RETURN nineties.title "
}'
```
This is the body of the request and is where the Query API looks for what it needs to do. In our example case, it's a single Cypher statement

```TEXT 
MATCH (nineties:Movie) WHERE nineties.released >= 1990 AND nineties.released < 2000 RETURN nineties.title
```

The Query API only accepts a single Cypher statement in a request. If you have several statements you want to perform you will need to send one request per statement or make use the Cypher CALL subquery facility.


## Next steps
In our next update on the Query API , we'll cover off
- using parameters
- execute the Cypher statement as a different Neo4j user to the one you used for authorisation
- When using Neo4j clusters, use the leader ( for writes ) or a follower ( for reads ). With server side routing enabled, this is taken care of automatically but there can be scenarios where you want to control this.

Until then, please try out the Query API and let us know how you get on.

Laters

JG
